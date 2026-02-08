from __future__ import annotations

from fastapi import FastAPI

from .api.documents import router as documents_router
from .api.health import router as health_router
from .config import Settings
from .database import Database
from . import models
from .services.storage import FileStorageService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_directories()

    database = Database(settings.database_url)
    database.init_schema()

    app = FastAPI(title=settings.app_name, version="0.2.0")
    app.state.settings = settings
    app.state.database = database
    app.state.storage_service = FileStorageService(settings.upload_dir)

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)

    return app


app = create_app()
