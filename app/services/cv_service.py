from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.pdf_builder import build_cv_pdf
from app.repositories.profile_repository import profile_repository
from app.schemas.cv import TailoredCV
from app.services.ollama_service import ollama_service
from app.services.prompt_service import prompt_service


class CVService:
    @staticmethod
    def upper_camel_case(text: str, max_len: int = 40) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        words = re.findall(r"[A-Za-z0-9]+", text)
        parts = [
            w if (w.isupper() and len(w) <= 3) else w[0].upper() + w[1:].lower()
            for w in words
        ]
        return "".join(parts)[:max_len]

    @staticmethod
    def resolve_location(job_offer: str, profile: dict[str, Any]) -> tuple[str, str]:
        offer_lower = job_offer.lower()

        # 1. Si la vacante menciona Barranquilla o Atlántico
        if any(kw in offer_lower for kw in ("barranquilla", "atlantico", "atlántico")):
            return "Barranquilla, Colombia", "Presencial, híbrida, remota."

        # 2. Si la vacante menciona Bogotá
        if any(kw in offer_lower for kw in ("bogotá", "bogota", "cundinamarca")):
            return "Bogotá, Colombia", "Remota, híbrida, presencial."

        # 3. Por defecto (remoto general o vacantes nacionales)
        return (
            profile.get("location", "Barranquilla, Colombia"),
            profile.get(
                "availability",
                "Remota, híbrida, presencial. Disponibilidad para reubicación a nivel nacional.",
            ),
        )

    @staticmethod
    def _experience_sort_key(exp: dict[str, Any]) -> tuple[int, int, int]:
        section = exp.get("section", "").strip().lower()
        dates = exp.get("dates", "").strip().lower()

        # Solo los empleos profesionales actuales reciben prioridad.
        is_professional = section == "profesional"
        is_current = bool(
            re.search(
                r"\b(actualidad|actual|presente|present|current|currently)\b",
                dates,
            )
        )

        # Extraer el primer año como año de inicio.
        years = re.findall(r"\b(?:19|20)\d{2}\b", dates)
        start_year = int(years[0]) if years else 0

        return (
            0 if is_professional and is_current else 1,
            -start_year,
            settings.SECTION_ORDER.get(section, 99),
        )

    def build_filename(self, profile: dict[str, Any], tailored: dict[str, Any]) -> str:
        candidate = self.upper_camel_case(" ".join(profile["name"].split()[:2]))
        position = (
            self.upper_camel_case(tailored.get("offer_position", ""))
            or self.upper_camel_case(tailored["target_title"].split("|")[0])
            or "Postulacion"
        )
        return f"CV_{candidate}_{position}.pdf"

    def generate_cv_for_offer(self, job_offer: str) -> tuple[Path, str]:
        profile = profile_repository.load_profile()
        profile_facts = profile_repository.get_profile_for_prompt(profile)

        prompt = prompt_service.build_tailoring_prompt(job_offer, profile_facts)
        tailored_cv: TailoredCV = ollama_service.generate_tailored_cv(prompt, profile)
        tailored = tailored_cv.model_dump()

        # Sincronizar el título visible en el CV con el nombre del puesto de la vacante.
        if tailored.get("offer_position") and len(tailored["offer_position"].strip()) >= 3:
            tailored["target_title"] = tailored["offer_position"].strip()

        focus = tailored["focus"]

        # Resolver ubicación dinámica según la oferta.
        location, availability = self.resolve_location(job_offer, profile)

        # Enriquecer con los datos de contacto y educación.
        tailored["contact"] = {
            key: profile[key]
            for key in ("name", "email", "phone", "portfolio", "linkedin")
        }
        tailored["contact"]["location"] = location
        tailored["contact"]["availability"] = availability
        tailored["languages"] = profile["languages"]
        tailored["education_text"] = profile["education"]
        tailored["experiences"] = []

        exp_by_id = {item["id"]: item for item in profile["experience"]}

        # Ordenar las experiencias seleccionadas:
        # 1. Empleo profesional actual.
        # 2. Las demás experiencias por fecha más reciente.
        # 3. La sección como criterio secundario.
        selected_ids = sorted(
            tailored["selected_experience_ids"],
            key=lambda exp_id: self._experience_sort_key(exp_by_id[exp_id]),
        )

        for exp_id in selected_ids:
            source = exp_by_id[exp_id]
            bullets = tailored["experience_bullets"].get(exp_id, [])

            if not bullets:
                fallback = (
                    source.get("bullets_fullstack")
                    if focus in ("fullstack", "backend")
                    else None
                ) or source["bullets"]
                bullets = fallback[:3]

            tailored["experiences"].append(
                {
                    "title": (
                        source.get("title_fullstack", source["title"])
                        if focus in ("fullstack", "backend")
                        else source["title"]
                    ),
                    "company": source["company"],
                    "dates": source["dates"],
                    "type": source["type"],
                    "section": source.get("section", ""),
                    "technologies": source["technologies"],
                    "bullets": bullets[:5],
                }
            )

        filename = self.build_filename(profile, tailored)
        output_path = settings.OUTPUT_DIR / filename

        build_cv_pdf(profile, tailored, output_path)
        return output_path, filename


cv_service = CVService()
