from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_settings, get_vector_store
from ..schemas import HealthResponse
from ..services.vector_store import VectorStoreProtocol

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    session: Session = Depends(get_db_session),
    settings=Depends(get_settings),
    vector_store: VectorStoreProtocol = Depends(get_vector_store),
) -> HealthResponse:
    status = "ok"
    services = {
        "database": "ok",
        "vector_store": "ok" if vector_store.ping() else "down",
        "gemini": "ok" if settings.gemini_api_key else "missing_api_key",
    }

    try:
        session.execute(text("SELECT 1"))
    except Exception:
        status = "degraded"
        services["database"] = "down"

    if services["vector_store"] != "ok":
        status = "degraded"

    return HealthResponse(status=status, services=services)
