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


class OllamaService:
    label: str = "Ollama local o cloud"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or settings.OLLAMA_BASE_URL
        ).rstrip("/")

        self.model = (model or settings.OLLAMA_MODEL).strip()

        # La API key es opcional.
        # Si no se proporciona, utiliza la configurada en settings.
        self.api_key = (
            api_key if api_key is not None else settings.OLLAMA_API_KEY
        ).strip()

    @property
    def default_model(self) -> str:
        return self.model

    def _fallback_models(self) -> list[LLMModel]:
        if not self.model:
            return []

        return [
            LLMModel(
                id=self.model,
                name=self.model,
                recommended=True,
            )
        ]

    def list_models(self) -> list[LLMModel]:
        """Obtiene el catálogo de modelos instalados o disponibles."""

        url = f"{self.base_url}/api/tags"
        headers: dict[str, str] = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=(3, 10),
            )
            response.raise_for_status()
            data = response.json()

        except (requests.RequestException, ValueError):
            return self._fallback_models()

        if not isinstance(data, dict):
            return self._fallback_models()

        raw_models = data.get("models") or []

        if not isinstance(raw_models, list):
            return self._fallback_models()

        models: list[LLMModel] = []

        for item in raw_models:
            if not isinstance(item, dict):
                continue

            model_id = item.get("name") or item.get("model")

            if not model_id:
                continue

            models.append(
                LLMModel(
                    id=model_id,
                    name=model_id,
                    recommended=model_id == self.model,
                )
            )

        # Si OLLAMA_MODEL apunta a un modelo que no aparece en /api/tags
        # (por ejemplo, un modelo cloud), lo agregamos al catálogo.
        if self.model and all(
            item.id != self.model for item in models
        ):
            models.insert(
                0,
                LLMModel(
                    id=self.model,
                    name=self.model,
                    recommended=True,
                ),
            )

        if not models:
            return self._fallback_models()

        models.sort(
            key=lambda item: (
                not item.recommended,
                item.name.lower(),
            )
        )
        return models

    def generate_tailored_cv(
        self,
        prompt: str,
        profile: dict[str, Any],
        model: str | None = None,
    ) -> TailoredCV:
        selected_model = (model or self.model).strip()

        if not selected_model:
            available_models = self.list_models()

            if not available_models:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "No hay modelos disponibles en Ollama. "
                        "Verifica que Ollama esté en ejecución o "
                        "define OLLAMA_MODEL en .env."
                    ),
                )

            selected_model = available_models[0].id

        schema = TailoredCV.model_json_schema()
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": selected_model,
            "stream": True,
            "format": schema,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Produces structured JSON for a CV. "
                        "Follow the schema strictly. "
                        "professional_summary must be between "
                        "500 and 700 characters. "
                        "Never invent information not present "
                        "in the source profile."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "options": {
                "temperature": settings.OLLAMA_TEMPERATURE,
                "num_ctx": settings.NUM_CTX,
            },
        }

        # --- AUTENTICACIÓN OPCIONAL ---
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        content_parts: list[str] = []
        thinking_started = False

        print("\n" + "=" * 70, flush=True)
        print(f"OLLAMA | URL: {self.base_url}", flush=True)
        print(f"OLLAMA | Modelo: {selected_model}", flush=True)
        print(
            "OLLAMA | Modo: "
            + ("Cloud con API key" if self.api_key else "Sin API key"),
            flush=True,
        )
        print("OLLAMA | Generando CV...", flush=True)
        print("=" * 70, flush=True)

        try:
            with requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=(10, 600),
            ) as response:
                response.raise_for_status()

                for raw_line in response.iter_lines(
                    decode_unicode=False
                ):
                    if not raw_line:
                        continue

                    if isinstance(raw_line, bytes):
                        line = raw_line.decode(
                            "utf-8",
                            errors="replace",
                        )
                    else:
                        line = raw_line

                    line = line.strip()

                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if "error" in chunk:
                        error_text = str(chunk["error"])
                        print(
                            f"\n[OLLAMA] Error en stream: {error_text}",
                            flush=True,
                        )

                        error_status = 502
                        lowered = error_text.lower()
                        detail = (
                            "Ollama reportó un error durante la generación. "
                            "Revisa la terminal para más detalles."
                        )

                        if any(
                            word in lowered
                            for word in (
                                "credit",
                                "subscription",
                                "usage",
                                "billing",
                            )
                        ):
                            error_status = 402
                            detail = (
                                "Ollama Cloud no tiene créditos o una "
                                "suscripción activa. Revisa tu plan en "
                                "ollama.com."
                            )

                        elif "not found" in lowered:
                            error_status = 404
                            detail = (
                                "No se encontró el modelo seleccionado en "
                                "Ollama. Elige otro modelo del catálogo."
                            )

                        raise HTTPException(
                            status_code=error_status,
                            detail=detail,
                        )

                    message = chunk.get("message", {})

                    # Algunos modelos devuelven razonamiento separado.
                    thinking = message.get("thinking", "")

                    if thinking:
                        if not thinking_started:
                            print(
                                "\n\n[RAZONAMIENTO]\n",
                                flush=True,
                            )
                            thinking_started = True

                        print(
                            thinking,
                            end="",
                            flush=True,
                        )

                    # Contenido de la respuesta.
                    fragment = message.get("content", "")

                    if fragment:
                        if thinking_started:
                            print(
                                "\n\n[JSON GENERADO]\n",
                                flush=True,
                            )
                            thinking_started = False

                        print(
                            fragment,
                            end="",
                            flush=True,
                        )

                        content_parts.append(fragment)

                    if chunk.get("done", False):
                        print(
                            "\n\n" + "=" * 70,
                            flush=True,
                        )
                        print(
                            "OLLAMA | Generación terminada.",
                            flush=True,
                        )

                        if "eval_count" in chunk:
                            print(
                                f"OLLAMA | Tokens: {chunk['eval_count']}",
                                flush=True,
                            )

                        if "total_duration" in chunk:
                            print(
                                "OLLAMA | Tiempo: "
                                f"{chunk['total_duration'] / 1e9:.2f}s",
                                flush=True,
                            )

                        print(
                            "=" * 70 + "\n",
                            flush=True,
                        )

        except requests.ConnectionError as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "No se pudo conectar con Ollama. "
                    "Verifica la URL y la conexión."
                ),
            ) from exc

        except requests.Timeout as exc:
            raise HTTPException(
                status_code=504,
                detail="Ollama tardó demasiado en responder.",
            ) from exc

        except requests.HTTPError as exc:
            detail = "Ollama devolvió un error HTTP."
            app_status = 502

            if exc.response is not None:
                status_code = exc.response.status_code
                upstream = exc.response.text.strip()[:1000]

                print(
                    f"\n[OLLAMA] HTTP {status_code}: {upstream}",
                    flush=True,
                )

                app_status = status_code

                if status_code == 401:
                    detail = (
                        "Ollama rechazó la autenticación. "
                        "Verifica OLLAMA_API_KEY."
                    )

                elif status_code == 402:
                    detail = (
                        "Ollama Cloud no tiene créditos o una suscripción "
                        "activa. Revisa tu plan en ollama.com."
                    )

                elif status_code == 403:
                    detail = (
                        "Ollama denegó la solicitud. "
                        "Verifica los permisos de tu cuenta."
                    )

                elif status_code == 404:
                    detail = (
                        "No se encontró el endpoint o modelo solicitado. "
                        "Verifica OLLAMA_BASE_URL y el modelo seleccionado."
                    )

                elif status_code == 429:
                    detail = (
                        "Ollama alcanzó el límite de uso. "
                        "Espera un momento o revisa tu plan."
                    )

                elif status_code == 503:
                    detail = (
                        "Ollama está experimentando alta demanda. "
                        "Espera unos minutos y vuelve a intentarlo."
                    )

                elif status_code >= 500:
                    detail = (
                        "Ollama no pudo completar la solicitud por un "
                        "problema temporal. Intenta de nuevo en unos minutos."
                    )

                else:
                    detail = (
                        f"Ollama devolvió un error HTTP {status_code}. "
                        "Revisa la terminal para más detalles."
                    )

            raise HTTPException(
                status_code=app_status,
                detail=detail,
            ) from exc

        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Error en la transmisión con Ollama: {exc}",
            ) from exc

        raw_content = "".join(content_parts)

        if not raw_content.strip():
            raise HTTPException(
                status_code=502,
                detail="Ollama no devolvió contenido.",
            )

        # --- PARSEAR, VALIDAR Y SANEAR RESPUESTA ---
        try:
            cv = parse_and_validate_cv(raw_content, profile)

        except (
            json.JSONDecodeError,
            ValidationError,
            ValueError,
        ) as exc:
            print(
                f"\n[OLLAMA] Error validando respuesta: {exc}",
                flush=True,
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "Ollama no devolvió un JSON válido. "
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


ollama_service = OllamaService()