from __future__ import annotations

import json
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import google.generativeai as genai
from PIL import Image


class MissingApiKeyError(RuntimeError):
    pass


class GeminiResponseParseError(RuntimeError):
    pass


@dataclass
class GeminiClient:
    api_key: str
    model_name: str
    embedding_model: str

    def __post_init__(self) -> None:
        if not self.api_key:
            raise MissingApiKeyError(
                "GEMINI_API_KEY veya GOOGLE_API_KEY tanimli degil."
            )
        genai.configure(api_key=self.api_key)
        self._text_model = genai.GenerativeModel(self.model_name)

    def extract_text_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        prompt = (
            "Bu gorseldeki tum metni eksiksiz olarak cikar. "
            "Yorum ekleme, sadece metni dondur."
        )
        image = Image.open(BytesIO(image_bytes))
        response = self._text_model.generate_content(
            [prompt, image],
            generation_config={"temperature": 0.0},
        )
        text = getattr(response, "text", "") or ""
        return text.strip()

    def embed_texts(
        self,
        texts: list[str],
        *,
        task_type: str = "retrieval_document",
    ) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            response = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type=task_type,
            )
            embedding = response.get("embedding")
            if not embedding:
                raise RuntimeError("Gemini embedding yaniti bos geldi")
            vectors.append(list(embedding))
        return vectors

    def answer_question(self, question: str, context_items: list[dict[str, Any]]) -> dict[str, Any]:
        context_lines = []
        for item in context_items:
            context_lines.append(
                f"[{item['cid']}] dosya={item['filename']} sayfa={item['page']} metin={item['text']}"
            )

        prompt = (
            "Yalnizca asagidaki baglamdan yararlanarak soruyu cevapla. "
            "Baglam disinda bilgi uretme. "
            "Cevaplayamazsan tam olarak 'Bu bilgi belgede bulunamadi.' yaz.\n\n"
            "JSON formati DISINDA cikti verme.\n"
            "JSON semasi: {\"answer\": string, \"citation_ids\": string[]}\n"
            "Her iddia icin en az bir citation id ekle.\n\n"
            f"Soru: {question}\n\n"
            "Baglam:\n"
            + "\n".join(context_lines)
        )

        response = self._text_model.generate_content(
            prompt,
            generation_config={"temperature": 0.1},
        )
        raw_text = (getattr(response, "text", "") or "").strip()
        return self._parse_json_response(raw_text)

    def _parse_json_response(self, raw_text: str) -> dict[str, Any]:
        if not raw_text:
            raise GeminiResponseParseError("Gemini bos cevap dondurdu")

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise GeminiResponseParseError("Gemini cevabi JSON degil")

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise GeminiResponseParseError("Gemini JSON parse edilemedi") from exc
