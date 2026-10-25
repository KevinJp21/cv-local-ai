from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class TailoredCV(BaseModel):
    offer_position: str = Field(
        min_length=2,
        max_length=80,
        description=(
            "Nombre del puesto tal como aparece en la oferta, sin empresa, "
            "ciudad, modalidad ni seniority entre paréntesis."
        ),
    )
    focus: Literal["frontend", "backend", "fullstack"] = Field(
        description="Enfoque del CV según lo que pide la oferta."
    )
    target_title: str = Field(
        min_length=2,
        max_length=80,
        description="Solo el nombre del cargo. Sin tecnologías ni separadores.",
    )
    professional_summary: str = Field(
        min_length=500,
        max_length=700,
        description=(
            "Perfil profesional adaptado a la oferta. "
            "Exactamente entre 500 y 700 caracteres (incluyendo espacios). "
            "Si el texto es más corto, amplíalo con información relevante del perfil. "
            "Si es más largo, condénsalo."
        ),
    )
    skill_groups: dict[str, list[str]]
    selected_experience_ids: list[str]
    experience_bullets: dict[str, list[str]]
    education_text: str = Field(min_length=5, max_length=300)
    languages: list[str]
    keywords_used: list[str] = []
