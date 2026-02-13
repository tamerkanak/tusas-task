from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401
from .api.documents import router as documents_router
from .api.health import router as health_router
from .api.questions import router as questions_router
from .config import Settings
from .database import Database
from .services.gemini import GeminiClient
from .services.storage import FileStorageService
from .services.vector_store import (
    ChromaVectorStore,
    LocalJsonVectorStore,
    UnavailableVectorStore,
    VectorStoreProtocol,
)


def configure_logging(environment: str) -> None:
    level = logging.DEBUG if environment == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_app(
    settings: Settings | None = None,
    *,
    vector_store: VectorStoreProtocol | None = None,
    gemini_client: GeminiClient | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_directories()
    configure_logging(settings.environment)

    database = Database(settings.database_url)
    database.init_schema()

    app = FastAPI(title=settings.app_name, version="0.3.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = settings
    app.state.database = database
    app.state.storage_service = FileStorageService(settings.upload_dir)
    if vector_store is not None:
        app.state.vector_store = vector_store
    else:
        try:
            app.state.vector_store = ChromaVectorStore(settings.chroma_dir)
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "Chroma kullanilamadi, LocalJsonVectorStore devreye alindi: %s",
                exc,
            )
            try:
                app.state.vector_store = LocalJsonVectorStore(
                    settings.data_dir / "local_vectors.json"
                )
            except Exception as inner_exc:
                app.state.vector_store = UnavailableVectorStore(str(inner_exc))
    if gemini_client is not None:
        app.state.gemini_client = gemini_client

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)
    app.include_router(questions_router, prefix=settings.api_prefix)

    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        @app.get("/", include_in_schema=False)
        def ui_index() -> FileResponse:
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()
