from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    PROJECT_NAME: str = "CV Local AI"
    VERSION: str = "0.2.0"

    ROOT_DIR: Path = ROOT_DIR
    DATA_PATH: Path = ROOT_DIR / "data" / "cv_base.json"
    OUTPUT_DIR: Path = ROOT_DIR / "outputs"
    TEMPLATES_DIR: Path = ROOT_DIR / "app" / "templates"
    STATIC_DIR: Path = ROOT_DIR / "app" / "static"

    # Ollama: local o cloud
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434",
    ).rstrip("/")

    OLLAMA_MODEL: str = os.getenv(
        "OLLAMA_MODEL",
        "",
    ).strip()

    # Opcional: dejar vacío para Ollama local
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "").strip()

    OLLAMA_TEMPERATURE: float = float(
        os.getenv("OLLAMA_TEMPERATURE", "0.4")
    )
    NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "12000"))

    # Proveedor de LLM: "ollama" o "gemini".
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    # Google Gemini (Google AI Studio)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_TEMPERATURE: float = float(
        os.getenv("GEMINI_TEMPERATURE", "1.0")
    )
    GEMINI_INCLUDE_THOUGHTS: bool = os.getenv(
        "GEMINI_INCLUDE_THOUGHTS",
        "true",
    ).strip().lower() in {"1", "true", "yes", "on"}
    GEMINI_BASE_URL: str = os.getenv(
        "GEMINI_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta",
    ).rstrip("/")
    GEMINI_MAX_OUTPUT_TOKENS: int = int(
        os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192")
    )

    SECTION_ORDER: dict[str, int] = {
        "profesional": 0,
        "freelance": 1,
        "proyectos": 2,
    }


settings = Settings()
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
