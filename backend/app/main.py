from __future__ import annotations

from fastapi import FastAPI

from . import models
from .api.documents import router as documents_router
from .api.health import router as health_router
from .api.questions import router as questions_router
from .config import Settings
from .database import Database
from .services.storage import FileStorageService
from .services.vector_store import ChromaVectorStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_directories()

    database = Database(settings.database_url)
    database.init_schema()

    app = FastAPI(title=settings.app_name, version="0.3.0")
    app.state.settings = settings
    app.state.database = database
    app.state.storage_service = FileStorageService(settings.upload_dir)
    app.state.vector_store = ChromaVectorStore(settings.chroma_dir)

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)
    app.include_router(questions_router, prefix=settings.api_prefix)

    return app


app = create_app()
