from __future__ import annotations

import json
from typing import Any

import requests
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.cv import TailoredCV
from app.services.llm_base import LLMModel
from app.services.llm_response import parse_and_validate_cv


GEMINI_CATALOG: tuple[LLMModel, ...] = (
    LLMModel(
        id="gemini-3.8-flash",
        name="Gemini 3.8 Flash",
        recommended=True,
    ),
    LLMModel(
        id="gemini-3.7-flash",
        name="Gemini 3.7 Flash",
    ),
    LLMModel(
        id="gemini-3.6-flash",
        name="Gemini 3.6 Flash",
    ),
    LLMModel(
        id="gemini-3.5-flash",
        name="Gemini 3.5 Flash",
    ),
    LLMModel(
        id="gemini-3.5-flash-lite",
        name="Gemini 3.5 Flash-Lite",
    ),
    LLMModel(
        id="gemini-3.1-flash-lite",
        name="Gemini 3.1 Flash-Lite",
    ),
    LLMModel(
        id="gemini-3.1-pro-preview",
        name="Gemini 3.1 Pro (Preview)",
    ),
    LLMModel(
        id="gemini-3-flash-preview",
        name="Gemini 3 Flash (Preview)",
    ),
)

_BLOCKED_FINISH_REASONS = {
    "SAFETY",
    "RECITATION",
    "BLOCKLIST",
    "PROHIBITED_CONTENT",
    "SPII",
}


class GeminiService:
    label: str = "Google Gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = (
            api_key if api_key is not None else settings.GEMINI_API_KEY
        ).strip()

        self.model = (model or GEMINI_CATALOG[0].id).strip()

        self.base_url = (
            base_url or settings.GEMINI_BASE_URL
        ).rstrip("/")

    @property
    def default_model(self) -> str:
        return self.model

    def list_models(self) -> list[LLMModel]:
        return list(GEMINI_CATALOG)

    @staticmethod
    def _endpoint_for(
        base_url: str,
        model: str,
        *,
        stream: bool = False,
    ) -> str:
        normalized = model

        if normalized.startswith("models/"):
            normalized = normalized[len("models/") :]

        method = "streamGenerateContent" if stream else "generateContent"

        return f"{base_url}/models/{normalized}:{method}"

    @property
    def endpoint(self) -> str:
        return self._endpoint_for(self.base_url, self.model)

    def _resolve_model(self, model: str | None) -> str:
        selected = (model or self.model).strip()
        valid_models = {item.id for item in GEMINI_CATALOG}

        if selected not in valid_models:
            available = ", ".join(item.id for item in GEMINI_CATALOG)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Modelo Gemini no válido: {selected}. "
                    f"Usa uno de: {available}."
                ),
            )

        return selected

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or []

        if not candidates:
            feedback = data.get("promptFeedback") or {}
            reason = feedback.get("blockReason") or "sin candidatos"
            raise ValueError(
                f"Gemini no devolvió candidatos ({reason})."
            )

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason") or ""

        if finish_reason in _BLOCKED_FINISH_REASONS:
            raise ValueError(
                "Gemini bloqueó la respuesta "
                f"(finishReason={finish_reason})."
            )

        parts = (candidate.get("content") or {}).get("parts") or []
        texts: list[str] = []

        for part in parts:
            # Las partes marcadas como "thought" son razonamiento interno.
            if part.get("thought"):
                continue

            text = part.get("text")

            if text:
                texts.append(text)

        content = "".join(texts).strip()

        if not content:
            raise ValueError(
                "Gemini no devolvió texto "
                f"(finishReason={finish_reason or 'desconocido'})."
            )

        return content

    @staticmethod
    def _process_stream(response: requests.Response) -> str:
        content_parts: list[str] = []
        thinking_started = False
        text_started = False
        usage: dict[str, Any] = {}
        finish_reason = ""

        for raw_line in response.iter_lines(decode_unicode=False):
            if not raw_line:
                continue

            if isinstance(raw_line, bytes):
                line = raw_line.decode("utf-8", errors="replace")
            else:
                line = raw_line

            line = line.strip()

            if not line.startswith("data:"):
                continue

            payload = line[len("data:") :].strip()

            if not payload or payload == "[DONE]":
                continue

            try:
                chunk = json.loads(payload)
            except json.JSONDecodeError:
                continue

            usage_metadata = chunk.get("usageMetadata")

            if usage_metadata:
                usage = usage_metadata

            candidates = chunk.get("candidates") or []

            if not candidates:
                feedback = chunk.get("promptFeedback") or {}
                reason = feedback.get("blockReason")

                if reason:
                    raise ValueError(
                        f"Gemini bloqueó la respuesta ({reason})."
                    )

                continue

            candidate = candidates[0]
            finish_reason = (
                candidate.get("finishReason") or finish_reason
            )

            if finish_reason in _BLOCKED_FINISH_REASONS:
                raise ValueError(
                    "Gemini bloqueó la respuesta "
                    f"(finishReason={finish_reason})."
                )

            parts = (candidate.get("content") or {}).get("parts") or []

            for part in parts:
                text = part.get("text")

                if not text:
                    continue

                if part.get("thought"):
                    if not thinking_started:
                        print("\n\n[RAZONAMIENTO]\n", flush=True)
                        thinking_started = True

                    print(text, end="", flush=True)
                    continue

                if not text_started:
                    print("\n\n[JSON GENERADO]\n", flush=True)
                    text_started = True

                print(text, end="", flush=True)
                content_parts.append(text)

        print("\n\n" + "=" * 70, flush=True)
        print("GEMINI | Generación terminada.", flush=True)

        total_tokens = usage.get("totalTokenCount")

        if total_tokens is not None:
            print(f"GEMINI | Tokens: {total_tokens}", flush=True)

        if finish_reason:
            print(f"GEMINI | finishReason: {finish_reason}", flush=True)

        print("=" * 70, flush=True)

        return "".join(content_parts).strip()

    def generate_tailored_cv(
        self,
        prompt: str,
        profile: dict[str, Any],
        model: str | None = None,
    ) -> TailoredCV:
        if not self.api_key:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Falta GEMINI_API_KEY. Agrégala en .env o usa "
                    "LLM_PROVIDER=ollama."
                ),
            )

        selected_model = self._resolve_model(model)
        endpoint = self._endpoint_for(
            self.base_url,
            selected_model,
            stream=True,
        )

        generation_config: dict[str, Any] = {
            "temperature": settings.GEMINI_TEMPERATURE,
            "responseMimeType": "application/json",
            "maxOutputTokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
        }

        if settings.GEMINI_INCLUDE_THOUGHTS:
            generation_config["thinkingConfig"] = {
                "includeThoughts": True,
            }

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "Devuelve únicamente un objeto JSON válido. "
                            "No agregues explicaciones ni bloques Markdown."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": generation_config,
        }

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key,
        }

        print("\n" + "=" * 70, flush=True)
        print(f"GEMINI | URL: {self.base_url}", flush=True)
        print(f"GEMINI | Modelo: {selected_model}", flush=True)
        print("GEMINI | Generando CV...", flush=True)
        print("=" * 70, flush=True)

        response: requests.Response | None = None

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                params={"alt": "sse"},
                stream=True,
                timeout=(10, 600),
            )
            response.raise_for_status()
            raw_content = self._process_stream(response)

        except requests.ConnectionError as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "No se pudo conectar con Gemini. "
                    "Verifica tu conexión a internet."
                ),
            ) from exc

        except requests.Timeout as exc:
            raise HTTPException(
                status_code=504,
                detail="Gemini tardó demasiado en responder.",
            ) from exc

        except requests.HTTPError as exc:
            detail = "Gemini devolvió un error HTTP."
            app_status = 502

            if exc.response is not None:
                status_code = exc.response.status_code
                upstream = exc.response.text.strip()[:1000]

                print(
                    f"\n[GEMINI] HTTP {status_code}: {upstream}",
                    flush=True,
                )

                app_status = status_code

                if status_code in (401, 403):
                    detail = (
                        "Gemini rechazó la API key o los permisos. "
                        "Verifica GEMINI_API_KEY."
                    )

                elif status_code == 404:
                    detail = (
                        "No se encontró el modelo Gemini seleccionado. "
                        "Elige otro modelo del catálogo."
                    )

                elif status_code == 429:
                    detail = (
                        "Gemini alcanzó el límite de cuota. "
                        "Espera un momento o revisa tu plan."
                    )

                elif status_code == 503:
                    detail = (
                        "Gemini está experimentando alta demanda en este "
                        "momento. Espera unos minutos y vuelve a intentarlo."
                    )

                elif status_code >= 500:
                    detail = (
                        "Gemini no pudo completar la solicitud por un "
                        "problema temporal. Intenta de nuevo en unos minutos."
                    )

                elif status_code == 400:
                    if (
                        "API_KEY_INVALID" in upstream
                        or "API key not valid" in upstream
                    ):
                        app_status = 401
                        detail = (
                            "Gemini rechazó la API key. "
                            "Verifica GEMINI_API_KEY."
                        )
                    else:
                        detail = (
                            "Gemini rechazó la solicitud. "
                            "Revisa la terminal para más detalles."
                        )

                else:
                    detail = (
                        f"Gemini devolvió un error HTTP {status_code}. "
                        "Revisa la terminal para más detalles."
                    )

            raise HTTPException(
                status_code=app_status,
                detail=detail,
            ) from exc

        except requests.RequestException as exc:
            print(
                f"\n[GEMINI] Error de transmisión: {exc}",
                flush=True,
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "Se interrumpió la conexión con Gemini. "
                    "Intenta de nuevo en unos minutos."
                ),
            ) from exc

        except ValueError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc

        finally:
            if response is not None:
                response.close()

        if not raw_content:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Gemini no devolvió contenido. "
                    "Intenta de nuevo o elige otro modelo."
                ),
            )

        try:
            cv = parse_and_validate_cv(raw_content, profile)

        except (
            json.JSONDecodeError,
            ValidationError,
            ValueError,
        ) as exc:
            print(
                f"\n[GEMINI] Error validando respuesta: {exc}",
                flush=True,
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "Gemini no devolvió un JSON válido. "
                    "Revisa la terminal."
                ),
            ) from exc

        if not cv.selected_experience_ids:
            raise HTTPException(
                status_code=502,
                detail=(
                    "El modelo no seleccionó experiencias válidas."
                ),
            )

        return cv


gemini_service = GeminiService()
