from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# A partir de estas palabras termina el nombre del puesto y empiezan los
# requisitos, tecnologías o condiciones de la oferta.
_TITLE_STOP_WORDS = re.compile(
    r"\b(?:"
    r"experiencia|con|manejo|conocimientos?|requisitos?|funciones?|"
    r"responsabilidades?|modalidad|jornada|salario|contrato|trabajo|"
    r"remoto|remota|h[ií]brid[oa]|presencial|tiempo completo|"
    r"medio tiempo|ubicaci[oó]n|ciudad|sede|empresa|compa[ñn][ií]a|"
    r"sector|vacante"
    r")\b",
    re.IGNORECASE,
)

# Separadores que suelen introducir la lista de tecnologías.
_TITLE_SEPARATORS = re.compile(
    r"\s*(?:\||·|•|;|:|–|—|,|\s+/\s+|\s+-\s+|\s+\+\s+)\s*"
)

# Tecnologías que pueden aparecer al final del título y deben eliminarse
# cuando acompañan al cargo ("Desarrollador Frontend React").
_TRAILING_TECH = {
    ".net",
    "android",
    "angular",
    "api",
    "asp.net",
    "aws",
    "azure",
    "bootstrap",
    "c#",
    "core",
    "css",
    "css3",
    "docker",
    "django",
    "flask",
    "graphql",
    "html",
    "html5",
    "ios",
    "java",
    "javascript",
    "kubernetes",
    "laravel",
    "liquid",
    "mongodb",
    "mysql",
    "next.js",
    "nextjs",
    "node.js",
    "nodejs",
    "php",
    "postgresql",
    "python",
    "react",
    "redux",
    "remix",
    "rest",
    "sass",
    "shopify",
    "spring",
    "sql",
    "svelte",
    "tailwind",
    "typescript",
    "vue",
}


def _clean_position_title(value: str) -> str:
    """Extrae solo el cargo y descarta tecnologías y condiciones.

    "Desarrollador full stack experiencia laravel + angular + mySQL +
     API REST trabajo híbrido" -> "Desarrollador full stack"
    """
    text = re.sub(r"\s+", " ", value).strip()
    if not text:
        return "Postulación"

    # Quita etiquetas tipo "Cargo: Desarrollador Full Stack".
    text = re.sub(
        r"^\s*(?:cargo|puesto|vacante|rol|posici[oó]n|t[ií]tulo)\s*[:\-–]\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Quita aclaraciones entre paréntesis: "Desarrollador (React)".
    text = re.sub(r"[\(\[\{][^\)\]\}]*[\)\]\}]", " ", text)

    # Corta la lista de tecnologías separada por |, ·, +, etc.
    text = _TITLE_SEPARATORS.split(text, maxsplit=1)[0]

    # Corta en la primera palabra que ya no pertenece al cargo.
    stop_match = _TITLE_STOP_WORDS.search(text)
    if stop_match:
        text = text[: stop_match.start()]

    text = re.sub(r"\s+", " ", text).strip(" .,;:|-–—•·+")
    words = text.split()

    # Elimina tecnologías al final, pero nunca deja el cargo con una sola
    # palabra ("Desarrollador .NET" se conserva tal cual).
    while len(words) > 2 and words[-1].lower() in _TRAILING_TECH:
        words.pop()

    # Límite de seguridad para no volver a superar el máximo del esquema.
    words = words[:6]
    text = " ".join(words)

    if len(text) > 70:
        text = text[:70].rsplit(" ", 1)[0].strip()

    return text or "Postulación"


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

    @field_validator("offer_position", "target_title", mode="before")
    @classmethod
    def _normalize_position(cls, value: object) -> object:
        if isinstance(value, str):
            return _clean_position_title(value)
        return value
