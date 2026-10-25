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
            
        # 2. Si la vacante menciona Bogotá o Cundinamarca
        if any(kw in offer_lower for kw in ("bogota", "bogotá", "cundinamarca")):
            return "Bogotá, Colombia", "Remota, híbrida, presencial."
            
        # 3. Por defecto (remoto general o vacantes nacionales)
        return (
            profile.get("location", "Bogotá, Colombia"),
            profile.get("availability", "Remota, híbrida, presencial. Disponibilidad para reubicación a nivel nacional.")
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

        # Sincronizar el título visible en el CV con el nombre del puesto de la vacante
        if tailored.get("offer_position") and len(tailored["offer_position"].strip()) >= 3:
            tailored["target_title"] = tailored["offer_position"].strip()

        focus = tailored["focus"]

        # Resolver ubicación dinámica entre Barranquilla y Bogotá según la oferta
        location, availability = self.resolve_location(job_offer, profile)

        # Enriquecer con los datos de contacto y educación
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

        selected_ids = sorted(
            tailored["selected_experience_ids"],
            key=lambda i: settings.SECTION_ORDER.get(exp_by_id[i].get("section", ""), 99),
        )

        for exp_id in selected_ids:
            source = exp_by_id[exp_id]
            bullets = tailored["experience_bullets"].get(exp_id, [])
            if not bullets:
                fallback = (
                    source.get("bullets_fullstack") if focus in ("fullstack", "backend") else None
                ) or source["bullets"]
                bullets = fallback[:3]

            tailored["experiences"].append({
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
            })

        filename = self.build_filename(profile, tailored)
        output_path = settings.OUTPUT_DIR / filename

        build_cv_pdf(profile, tailored, output_path)
        return output_path, filename


cv_service = CVService()
