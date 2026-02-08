from __future__ import annotations

from sqlalchemy import text

from ..dependencies import get_db_session
from ..schemas import HealthResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_db_session)) -> HealthResponse:
    status = "ok"
    services = {"database": "ok", "vector_store": "bootstrapping", "gemini": "bootstrapping"}

    try:
        session.execute(text("SELECT 1"))
    except Exception:
        status = "degraded"
        services["database"] = "down"

    return HealthResponse(status=status, services=services)
