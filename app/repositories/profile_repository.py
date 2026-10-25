from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import settings


class ProfileRepository:
    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or settings.DATA_PATH

    def load_profile(self) -> dict[str, Any]:
        with self.data_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_profile_for_prompt(self, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        if profile is None:
            profile = self.load_profile()

        experiences = []
        for item in profile.get("experience", []):
            exp: dict[str, Any] = {
                "id": item["id"],
                "tipo": item["type"],
                "seccion": item.get("section", ""),
                "cargo": item["title"],
                "empresa_o_proyecto": item["company"],
                "fechas": item["dates"],
                "tecnologias": item["technologies"],
                "hechos": item["bullets"],
            }
            if item.get("title_fullstack"):
                exp["cargo_fullstack"] = item["title_fullstack"]
            if item.get("bullets_fullstack"):
                exp["hechos_fullstack"] = item["bullets_fullstack"]
            experiences.append(exp)

        return {
            "resumen_frontend": profile.get("summary_frontend", ""),
            "resumen_fullstack": profile.get("summary_fullstack", ""),
            "habilidades_frontend": profile.get("skills_frontend", {}),
            "habilidades_fullstack": profile.get("skills", {}),
            "educacion": profile.get("education", ""),
            "idiomas": profile.get("languages", []),
            "experiencias": experiences,
        }


profile_repository = ProfileRepository()
