from __future__ import annotations

import json
import re
from typing import Any

import requests
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.cv import TailoredCV


class OllamaService:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or settings.OLLAMA_BASE_URL
        ).rstrip("/")

        self.model = model or settings.OLLAMA_MODEL

        # La API key es opcional.
        # Si no se proporciona, utiliza la configurada en settings.
        self.api_key = (
            api_key if api_key is not None else settings.OLLAMA_API_KEY
        ).strip()

    @staticmethod
    def extract_and_parse_json(
        raw_text: str,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        text = raw_text.strip()

        # Quitar delimitadores de Markdown si existen.
        if "```" in text:
            match = re.search(
                r"```(?:json)?\s*([\s\S]*?)\s*```",
                text,
                re.IGNORECASE,
            )
            if match:
                text = match.group(1).strip()

        # Si no empieza con {, buscar el primer { y el último }.
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")

            if start != -1 and end != -1:
                text = text[start : end + 1]

        data = json.loads(text)

        if not isinstance(data, dict):
            raise ValueError("El resultado no es un objeto JSON.")

        # --- NORMALIZADOR DE COMPATIBILIDAD (Gemma / Qwen / otros) ---

        # 1. Normalizar habilidades / skill_groups.
        if (
            "skill_groups" not in data
            and "habilidades" in data
            and isinstance(data["habilidades"], dict)
        ):
            data["skill_groups"] = data["habilidades"]

        elif (
            "skill_groups" not in data
            and "skills" in data
            and isinstance(data["skills"], dict)
        ):
            data["skill_groups"] = data["skills"]

        # 2. Normalizar focus.
        if "focus" not in data:
            title_lower = (
                data.get("target_title", "")
                + " "
                + data.get("offer_position", "")
            ).lower()

            if (
                "full" in title_lower
                or "fullstack" in title_lower
                or "full stack" in title_lower
            ):
                data["focus"] = "fullstack"

            elif "back" in title_lower:
                data["focus"] = "backend"

            else:
                data["focus"] = "frontend"

        # 3. Normalizar experiencias si vienen como lista.
        valid_ids = [
            item["id"]
            for item in profile.get("experience", [])
        ]

        if (
            "selected_experience_ids" not in data
            or not data["selected_experience_ids"]
        ):
            selected_ids = []
            bullets_dict = {}

            raw_exps = (
                data.get("experiences")
                or data.get("experiencias")
                or []
            )

            for exp in raw_exps:
                if not isinstance(exp, dict):
                    continue

                exp_id = exp.get("id")

                if not exp_id:
                    exp_text = (
                        str(exp.get("empresa_o_proyecto", ""))
                        + " "
                        + str(exp.get("company", ""))
                        + " "
                        + str(exp.get("cargo", ""))
                        + " "
                        + str(exp.get("title", ""))
                    ).lower()

                    for valid_id in valid_ids:
                        if valid_id.lower() in exp_text:
                            exp_id = valid_id
                            break

                if exp_id and exp_id in valid_ids:
                    if exp_id not in selected_ids:
                        selected_ids.append(exp_id)

                    bullets = (
                        exp.get("viñetas")
                        or exp.get("bullets")
                        or []
                    )

                    if isinstance(bullets, list) and bullets:
                        bullets_dict[exp_id] = [
                            str(bullet) for bullet in bullets
                        ]

            if selected_ids:
                data["selected_experience_ids"] = selected_ids

                if "experience_bullets" not in data:
                    data["experience_bullets"] = bullets_dict

        # 4. Normalizar educación e idiomas.
        if "education_text" not in data:
            data["education_text"] = (
                data.get("educacion")
                or profile.get("education", "")
            )

        if "languages" not in data:
            data["languages"] = (
                data.get("idiomas")
                or profile.get("languages", [])
            )

        return data

    def generate_tailored_cv(
        self,
        prompt: str,
        profile: dict[str, Any],
    ) -> TailoredCV:
        schema = TailoredCV.model_json_schema()
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
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
                "temperature": settings.TEMPERATURE,
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
        print(f"OLLAMA | Modelo: {self.model}", flush=True)
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

                for line in response.iter_lines(
                    decode_unicode=True
                ):
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if "error" in chunk:
                        raise HTTPException(
                            status_code=502,
                            detail=(
                                "Ollama reportó un error: "
                                f"{chunk['error']}"
                            ),
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

            if exc.response is not None:
                status_code = exc.response.status_code

                if status_code == 401:
                    detail = (
                        "Ollama rechazó la autenticación. "
                        "Verifica OLLAMA_API_KEY."
                    )

                elif status_code == 403:
                    detail = (
                        "Ollama denegó la solicitud. "
                        "Verifica los permisos de tu cuenta."
                    )

                elif status_code == 404:
                    detail = (
                        "No se encontró el endpoint o modelo solicitado. "
                        "Verifica OLLAMA_BASE_URL y OLLAMA_MODEL."
                    )

                else:
                    detail = (
                        f"Ollama HTTP {status_code}: "
                        f"{exc.response.text[:300]}"
                    )

            raise HTTPException(
                status_code=502,
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

        # --- PARSEAR Y VALIDAR RESPUESTA ---
        try:
            data = self.extract_and_parse_json(
                raw_content,
                profile,
            )

            cv = TailoredCV.model_validate(data)

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

        # --- SANEAR IDs ---
        valid_ids = {
            item["id"]
            for item in profile.get("experience", [])
        }

        cv.selected_experience_ids = [
            experience_id
            for experience_id in cv.selected_experience_ids
            if experience_id in valid_ids
        ]

        cv.experience_bullets = {
            experience_id: bullets
            for experience_id, bullets in cv.experience_bullets.items()
            if experience_id in valid_ids
        }

        if not cv.selected_experience_ids:
            raise HTTPException(
                status_code=502,
                detail=(
                    "El modelo no seleccionó experiencias válidas."
                ),
            )

        return cv


ollama_service = OllamaService()