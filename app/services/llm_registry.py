from __future__ import annotations

from fastapi import HTTPException

from app.core.config import settings
from app.services.gemini_service import gemini_service
from app.services.llm_base import LLMProvider
from app.services.ollama_service import ollama_service

# Para agregar un proveedor nuevo:
# 1. Crea su servicio con `model`, `label` y `generate_tailored_cv`.
# 2. Impórtalo y agrégalo a este diccionario.
_PROVIDERS: dict[str, LLMProvider] = {
    "ollama": ollama_service,
    "gemini": gemini_service,
}


def get_llm_service() -> LLMProvider:
    provider = settings.LLM_PROVIDER
    service = _PROVIDERS.get(provider)

    if service is None:
        available = ", ".join(sorted(_PROVIDERS))
        raise HTTPException(
            status_code=500,
            detail=(
                f"Proveedor LLM no soportado: {provider}. "
                f"Usa uno de: {available}."
            ),
        )

    return service
