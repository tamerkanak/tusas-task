from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import google.generativeai as genai
from PIL import Image


class MissingApiKeyError(RuntimeError):
    pass


@dataclass
class GeminiClient:
    api_key: str
    model_name: str

    def __post_init__(self) -> None:
        if not self.api_key:
            raise MissingApiKeyError(
                "GEMINI_API_KEY veya GOOGLE_API_KEY tanimli degil."
            )
        genai.configure(api_key=self.api_key)
        self._vision_model = genai.GenerativeModel(self.model_name)

    def extract_text_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        prompt = (
            "Bu gorseldeki tum metni eksiksiz olarak cikar. "
            "Yorum ekleme, sadece metni dondur."
        )
        image = Image.open(BytesIO(image_bytes))
        response = self._vision_model.generate_content(
            [prompt, image],
            generation_config={"temperature": 0.0},
        )
        text = getattr(response, "text", "") or ""
        return text.strip()
