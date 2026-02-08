from __future__ import annotations

import logging
from statistics import mean

from ..repositories import DocumentRepository
from ..schemas import AskResponse, Citation
from .gemini import GeminiClient
from .vector_store import RetrievedChunk, VectorStoreProtocol

logger = logging.getLogger(__name__)


class QAService:
    NO_EVIDENCE_ANSWER = "Bu bilgi belgede bulunamadi."

    def __init__(
        self,
        document_repository: DocumentRepository,
        vector_store: VectorStoreProtocol,
        ai_client: GeminiClient,
        retrieval_max_distance: float,
    ) -> None:
        self.document_repository = document_repository
        self.vector_store = vector_store
        self.ai_client = ai_client
        self.retrieval_max_distance = retrieval_max_distance

    def ask(self, question: str, document_ids: list[str], top_k: int) -> AskResponse:
        documents = self.document_repository.list_by_ids(document_ids)
        indexed_docs = {document.id: document for document in documents if document.status == "indexed"}

        if not indexed_docs:
            logger.info("QA no_evidence: indexed belge bulunamadi")
            return self._no_evidence_response()

        query_embedding = self.ai_client.embed_texts(
            [question],
            task_type="retrieval_query",
        )[0]
        retrieved = self.vector_store.query(
            query_embedding=query_embedding,
            document_ids=list(indexed_docs.keys()),
            top_k=max(top_k * 2, top_k),
        )

        filtered_chunks = [
            chunk for chunk in retrieved if chunk.distance <= self.retrieval_max_distance
        ][:top_k]

        if not filtered_chunks:
            logger.info("QA no_evidence: retrieval sonucu esik altinda")
            return self._no_evidence_response()

        context_items = []
        citation_map: dict[str, Citation] = {}
        for index, chunk in enumerate(filtered_chunks, start=1):
            cid = f"C{index}"
            context_items.append(
                {
                    "cid": cid,
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "page": chunk.page,
                    "text": chunk.text,
                }
            )
            citation_map[cid] = Citation(
                document_id=chunk.document_id,
                filename=chunk.filename,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                snippet=self._snippet(chunk.text),
            )

        model_output = self.ai_client.answer_question(question, context_items)
        answer = str(model_output.get("answer", "")).strip()
        selected_ids = model_output.get("citation_ids", [])

        if not isinstance(selected_ids, list):
            selected_ids = []

        citations = [citation_map[cid] for cid in selected_ids if cid in citation_map]

        if not citations or not answer:
            logger.info("QA no_evidence: citation veya cevap bos")
            return self._no_evidence_response(used_chunks=len(filtered_chunks))

        if answer.lower() == self.NO_EVIDENCE_ANSWER.lower():
            logger.info("QA no_evidence: model baglam disi oldugunu bildirdi")
            return self._no_evidence_response(used_chunks=len(filtered_chunks))

        confidence = self._calculate_confidence(filtered_chunks, citations)

        return AskResponse(
            answer=answer,
            mode="grounded_answer",
            citations=citations,
            confidence=confidence,
            used_chunks=len(filtered_chunks),
        )

    def _calculate_confidence(
        self,
        chunks: list[RetrievedChunk],
        citations: list[Citation],
    ) -> float:
        distance_by_chunk_id = {chunk.chunk_id: chunk.distance for chunk in chunks}
        cited_distances = [
            distance_by_chunk_id[citation.chunk_id]
            for citation in citations
            if citation.chunk_id in distance_by_chunk_id
        ]
        if not cited_distances:
            return 0.0

        avg_distance = mean(cited_distances)
        score = max(0.0, min(1.0, 1.0 - avg_distance))
        return round(score, 3)

    def _no_evidence_response(self, used_chunks: int = 0) -> AskResponse:
        return AskResponse(
            answer=self.NO_EVIDENCE_ANSWER,
            mode="no_evidence",
            citations=[],
            confidence=0.0,
            used_chunks=used_chunks,
        )

    @staticmethod
    def _snippet(text: str, size: int = 220) -> str:
        compact = " ".join(text.split())
        return compact[:size]
