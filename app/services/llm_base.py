from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas.cv import TailoredCV


@dataclass(frozen=True)
class LLMModel:
    """Opción de modelo que se muestra en el catálogo del proveedor."""

    id: str
    name: str
    recommended: bool = False


class LLMProvider(Protocol):
    """Contrato común para todos los proveedores de LLM."""

    model: str
    label: str

    @property
    def default_model(self) -> str:
        ...

    def list_models(self) -> list[LLMModel]:
        ...

    def generate_tailored_cv(
        self,
        prompt: str,
        profile: dict[str, Any],
        model: str | None = None,
    ) -> TailoredCV:
        ...
