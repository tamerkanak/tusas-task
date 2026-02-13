from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]


class MissingApiKeyError(RuntimeError):
    pass


class MissingDependencyError(RuntimeError):
    pass


class GeminiResponseParseError(RuntimeError):
    pass


logger = logging.getLogger(__name__)


class _AnswerPayload(BaseModel):
    answer: str
    citation_ids: list[str] = Field(default_factory=list)


def _normalize_task_type(task_type: str) -> str:
    normalized = task_type.strip()
    lowered = normalized.lower()
    mapping = {
        "retrieval_document": "RETRIEVAL_DOCUMENT",
        "retrieval_query": "RETRIEVAL_QUERY",
        "semantic_similarity": "SEMANTIC_SIMILARITY",
        "classification": "CLASSIFICATION",
        "clustering": "CLUSTERING",
    }
    return mapping.get(lowered, normalized)


@dataclass
class GeminiClient:
    api_key: str
    model_name: str
    embedding_model: str
    use_system_proxy: bool = False

    def __post_init__(self) -> None:
        if not self.api_key:
            raise MissingApiKeyError("GEMINI_API_KEY veya GOOGLE_API_KEY tanimli degil.")

        if genai is None or types is None:
            raise MissingDependencyError(
                "google-genai paketi yuklu degil. "
                "Lutfen `pip install -r backend/requirements.txt` calistirin."
            )

        if not self.use_system_proxy:
            self._clear_proxy_environment()

        self._client = genai.Client(api_key=self.api_key)

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def extract_text_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        prompt = (
            "Bu gorseldeki tum metni eksiksiz olarak cikar. "
            "Yorum ekleme, sadece metni dondur."
        )
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
            config=types.GenerateContentConfig(temperature=0.0),
        )
        return (getattr(response, "text", "") or "").strip()

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        prompt = (
            "Bu PDF belgesindeki tum metni eksiksiz cikar. "
            "Yorum ekleme, sadece metni dondur."
        )
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=[
                prompt,
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            ],
            config=types.GenerateContentConfig(temperature=0.0),
        )
        return (getattr(response, "text", "") or "").strip()

    def embed_texts(
        self,
        texts: list[str],
        *,
        task_type: str = "retrieval_document",
    ) -> list[list[float]]:
        if not texts:
            return []

        normalized_task = _normalize_task_type(task_type)
        response = self._client.models.embed_content(
            model=self.embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=normalized_task),
        )
        embeddings = getattr(response, "embeddings", None) or []
        vectors: list[list[float]] = []
        for embedding in embeddings:
            values = getattr(embedding, "values", None)
            if not values:
                raise RuntimeError("Gemini embedding yaniti bos geldi")
            vectors.append(list(values))

        if len(vectors) != len(texts):
            raise RuntimeError("Gemini embedding yaniti beklenen uzunlukta degil")

        return vectors

    def answer_question(
        self,
        question: str,
        context_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        context_lines = []
        for item in context_items:
            context_lines.append(
                f"[{item['cid']}] dosya={item['filename']} sayfa={item['page']} metin={item['text']}"
            )

        prompt = (
            "Yalnizca asagidaki baglamdan yararlanarak soruyu cevapla. "
            "Baglam disinda bilgi uretme. "
            "Cevaplayamazsan tam olarak 'Bu bilgi belgede bulunamadi.' yaz.\n\n"
            "Her iddia icin en az bir citation id ekle.\n\n"
            f"Soru: {question}\n\n"
            "Baglam:\n"
            + "\n".join(context_lines)
        )

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=_AnswerPayload,
            ),
        )

        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, BaseModel):
                return parsed.model_dump()
            if isinstance(parsed, dict):
                return parsed

        raw_text = (getattr(response, "text", "") or "").strip()
        if not raw_text:
            raise GeminiResponseParseError("Gemini bos cevap dondurdu")

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise GeminiResponseParseError("Gemini cevabi JSON parse edilemedi") from exc

    def _clear_proxy_environment(self) -> None:
        for key in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
        ):
            os.environ.pop(key, None)

