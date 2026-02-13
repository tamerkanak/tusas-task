from __future__ import annotations

import math

from backend.app.services.vector_store import RetrievedChunk


class FakeGeminiClient:
    def extract_text_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        return "Mock OCR metni"

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        return "Mock PDF metni"

    def embed_texts(self, texts: list[str], *, task_type: str = "retrieval_document") -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def answer_question(self, question: str, context_items: list[dict[str, object]]) -> dict[str, object]:
        lowered = question.lower()
        if "mars" in lowered:
            return {"answer": "Bu bilgi belgede bulunamadi.", "citation_ids": []}

        for item in context_items:
            cid = str(item["cid"])
            text = str(item["text"]).lower()
            if "ankara" in lowered and "ankara" in text:
                return {
                    "answer": "Belgeye gore Ankara bilgisi mevcut.",
                    "citation_ids": [cid],
                }
            if "ucak" in lowered and "ucak" in text:
                return {
                    "answer": "Belgede ucak bilgisi mevcut.",
                    "citation_ids": [cid],
                }

        if context_items:
            return {
                "answer": "Belgede ilgili bilgi bulundu.",
                "citation_ids": [str(context_items[0]["cid"])],
            }

        return {"answer": "Bu bilgi belgede bulunamadi.", "citation_ids": []}

    def _vectorize(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            1.0 if "ankara" in lowered else 0.0,
            1.0 if "istanbul" in lowered else 0.0,
            1.0 if "ucak" in lowered else 0.0,
            min(1.0, len(lowered) / 400.0),
        ]


class FakeVectorStore:
    def __init__(self) -> None:
        self._records: list[tuple[dict[str, object], list[float]]] = []

    def upsert(self, chunks: list[object], embeddings: list[list[float]]) -> None:
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            chunk_id = str(chunk.id)
            self._records = [record for record in self._records if record[0]["id"] != chunk_id]
            self._records.append(
                (
                    {
                        "id": chunk_id,
                        "document_id": str(chunk.document_id),
                        "filename": str(chunk.filename),
                        "page": chunk.page,
                        "text": str(chunk.text),
                    },
                    embedding,
                )
            )

    def query(self, query_embedding: list[float], document_ids: list[str], top_k: int) -> list[RetrievedChunk]:
        scored: list[tuple[float, dict[str, object]]] = []

        for payload, embedding in self._records:
            if payload["document_id"] not in document_ids:
                continue
            distance = self._cosine_distance(query_embedding, embedding)
            scored.append((distance, payload))

        scored.sort(key=lambda item: item[0])
        result: list[RetrievedChunk] = []
        for distance, payload in scored[:top_k]:
            result.append(
                RetrievedChunk(
                    chunk_id=str(payload["id"]),
                    document_id=str(payload["document_id"]),
                    filename=str(payload["filename"]),
                    page=payload["page"],
                    text=str(payload["text"]),
                    distance=distance,
                )
            )
        return result

    def ping(self) -> bool:
        return True

    def _cosine_distance(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 1.0
        similarity = dot / (norm_a * norm_b)
        return max(0.0, min(2.0, 1.0 - similarity))
