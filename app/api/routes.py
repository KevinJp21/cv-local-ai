from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.repositories.profile_repository import profile_repository
from app.services.cv_service import cv_service

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    profile = profile_repository.load_profile()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"profile": profile, "model": settings.OLLAMA_MODEL},
    )


@router.post("/generate")
def generate(job_offer: str = Form(...)):
    job_offer = job_offer.strip()
    if len(job_offer) < 80:
        raise HTTPException(
            status_code=400,
            detail="Pega la descripción completa de la oferta (mínimo 80 caracteres).",
        )
    if len(job_offer) > 25000:
        raise HTTPException(
            status_code=400,
            detail="La oferta es demasiado larga (máximo 25.000 caracteres).",
        )

    output_path, filename = cv_service.generate_cv_for_offer(job_offer)

    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
