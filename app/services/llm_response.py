from __future__ import annotations

import json
import re
from typing import Any

from app.schemas.cv import TailoredCV


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

    # --- NORMALIZADOR DE COMPATIBILIDAD (Gemma / Qwen / Gemini / otros) ---

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


def sanitize_tailored_cv(
    cv: TailoredCV,
    profile: dict[str, Any],
) -> TailoredCV:
    """Elimina IDs de experiencia que no existan en el perfil fuente."""

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

    return cv


def parse_and_validate_cv(
    raw_text: str,
    profile: dict[str, Any],
) -> TailoredCV:
    """Parsea, valida y sanea la respuesta de cualquier proveedor de LLM."""

    data = extract_and_parse_json(raw_text, profile)
    cv = TailoredCV.model_validate(data)
    return sanitize_tailored_cv(cv, profile)
