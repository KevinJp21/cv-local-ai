from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.repositories.profile_repository import profile_repository
from app.services.cv_service import cv_service
from app.services.llm_registry import get_llm_service

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


def _build_provider_context(
    selected_model: str | None = None,
) -> dict:
    provider = get_llm_service()
    models = provider.list_models()
    selected = (selected_model or provider.default_model).strip()

    if selected not in {item.id for item in models}:
        selected = models[0].id if models else ""

    return {
        "models": models,
        "selected_model": selected,
        "provider_label": provider.label,
    }


def _render_index(
    request: Request,
    *,
    job_offer: str = "",
    selected_model: str | None = None,
    error_message: str = "",
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profile": profile_repository.load_profile(),
            "job_offer": job_offer,
            "error_message": error_message,
            **_build_provider_context(selected_model),
        },
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return _render_index(request)


@router.post("/generate")
def generate(
    request: Request,
    job_offer: str = Form(...),
    model: str | None = Form(None),
):
    job_offer = job_offer.strip()
    model = (model or "").strip() or None

    try:
        if len(job_offer) < 80:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Pega la descripción completa de la oferta "
                    "(mínimo 80 caracteres)."
                ),
            )
        if len(job_offer) > 25000:
            raise HTTPException(
                status_code=400,
                detail=(
                    "La oferta es demasiado larga "
                    "(máximo 25.000 caracteres)."
                ),
            )
        if model and len(model) > 100:
            raise HTTPException(
                status_code=400,
                detail="El identificador del modelo no es válido.",
            )

        output_path, filename = cv_service.generate_cv_for_offer(
            job_offer,
            model=model,
        )

    except HTTPException as exc:
        return _render_index(
            request,
            job_offer=job_offer,
            selected_model=model,
            error_message=str(exc.detail),
            status_code=exc.status_code,
        )

    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
