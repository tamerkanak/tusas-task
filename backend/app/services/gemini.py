from __future__ import annotations

import json
import logging
import os
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


logger = logging.getLogger(__name__)


@dataclass
class GeminiClient:
    api_key: str
    model_name: str
    embedding_model: str
    use_system_proxy: bool = False

    def __post_init__(self) -> None:
        if not self.api_key:
            raise MissingApiKeyError(
                "GEMINI_API_KEY veya GOOGLE_API_KEY tanimli degil."
            )
        if not self.use_system_proxy:
            self._clear_proxy_environment()
        genai.configure(api_key=self.api_key)
        self.model_name = self._resolve_generation_model(self.model_name)
        self.embedding_model = self._resolve_embedding_model(self.embedding_model)
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

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        prompt = (
            "Bu PDF belgesindeki tum metni eksiksiz cikar. "
            "Yorum ekleme, sadece metni dondur."
        )
        response = self._text_model.generate_content(
            [
                prompt,
                {
                    "mime_type": "application/pdf",
                    "data": pdf_bytes,
                },
            ],
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

    def _resolve_generation_model(self, configured_name: str) -> str:
        models = self._list_models_safe()
        if not models:
            return configured_name

        exact = self._find_supported_model(models, configured_name, "generateContent")
        if exact:
            return exact

        fallback = self._pick_fallback_model(models, "generateContent", preferred_keyword="flash")
        if fallback:
            logger.warning(
                "Gemini generate model '%s' kullanilamadi, '%s' secildi.",
                configured_name,
                fallback,
            )
            return fallback

        return configured_name

    def _resolve_embedding_model(self, configured_name: str) -> str:
        models = self._list_models_safe()
        if not models:
            return configured_name

        exact = self._find_supported_model(models, configured_name, "embedContent")
        if exact:
            return exact

        fallback = self._pick_fallback_model(models, "embedContent")
        if fallback:
            logger.warning(
                "Gemini embedding model '%s' kullanilamadi, '%s' secildi.",
                configured_name,
                fallback,
            )
            return fallback

        return configured_name

    def _list_models_safe(self) -> list[Any]:
        try:
            return list(genai.list_models())
        except Exception as exc:
            logger.warning("Gemini model listesi alinamadi: %s", exc)
            return []

    def _find_supported_model(
        self,
        models: list[Any],
        configured_name: str,
        method: str,
    ) -> str | None:
        target = configured_name.removeprefix("models/")
        for model in models:
            name = getattr(model, "name", "")
            normalized = str(name).removeprefix("models/")
            methods = set(getattr(model, "supported_generation_methods", []) or [])
            if normalized == target and method in methods:
                return name
        return None

    def _pick_fallback_model(
        self,
        models: list[Any],
        method: str,
        preferred_keyword: str | None = None,
    ) -> str | None:
        candidates: list[str] = []
        for model in models:
            name = str(getattr(model, "name", ""))
            methods = set(getattr(model, "supported_generation_methods", []) or [])
            if method in methods:
                candidates.append(name)

        if not candidates:
            return None

        if preferred_keyword:
            for candidate in candidates:
                if preferred_keyword in candidate.lower():
                    return candidate

        return candidates[0]
