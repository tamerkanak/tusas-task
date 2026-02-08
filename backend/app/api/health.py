from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_settings
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    session: Session = Depends(get_db_session),
    settings=Depends(get_settings),
) -> HealthResponse:
    status = "ok"
    services = {
        "database": "ok",
        "vector_store": "bootstrapping",
        "gemini": "ok" if settings.gemini_api_key else "missing_api_key",
    }

    try:
        session.execute(text("SELECT 1"))
    except Exception:
        status = "degraded"
        services["database"] = "down"

    return HealthResponse(status=status, services=services)
