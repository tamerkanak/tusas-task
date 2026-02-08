from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_qa_service
from ..schemas import AskRequest, AskResponse
from ..services.qa import QAService

router = APIRouter(tags=["questions"])


@router.post("/questions", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    service: QAService = Depends(get_qa_service),
) -> AskResponse:
    return service.ask(
        question=payload.question,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )
