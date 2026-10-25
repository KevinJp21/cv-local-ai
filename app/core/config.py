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

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
    TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.4"))
    NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "12000"))

    SECTION_ORDER: dict[str, int] = {
        "profesional": 0,
        "freelance": 1,
        "proyectos": 2,
    }

settings = Settings()
settings.OUTPUT_DIR.mkdir(exist_ok=True)
