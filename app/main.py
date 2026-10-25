from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
    )

    if settings.STATIC_DIR.exists():
        application.mount(
            "/static",
            StaticFiles(directory=str(settings.STATIC_DIR)),
            name="static",
        )

    application.include_router(api_router)
    return application


app = create_app()
