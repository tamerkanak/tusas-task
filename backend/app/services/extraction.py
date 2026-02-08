from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .gemini import GeminiClient


@dataclass
class ExtractedSegment:
    page: int | None
    source: str
    text: str


class DocumentExtractor:
    def __init__(self, ai_client: GeminiClient, min_chars_before_ocr: int = 40) -> None:
        self.ai_client = ai_client
        self.min_chars_before_ocr = min_chars_before_ocr

    def extract(self, file_path: Path, file_type: str) -> list[ExtractedSegment]:
        normalized = file_type.lower()
        if normalized == "pdf":
            return self._extract_from_pdf(file_path)
        if normalized in {"jpg", "jpeg", "png"}:
            content = file_path.read_bytes()
            text = self.ai_client.extract_text_from_image(
                image_bytes=content,
                mime_type=f"image/{'jpeg' if normalized in {'jpg', 'jpeg'} else 'png'}",
            )
            return [ExtractedSegment(page=1, source="ocr", text=text)] if text else []

        raise ValueError(f"Desteklenmeyen dosya tipi: {file_type}")

    def _extract_from_pdf(self, file_path: Path) -> list[ExtractedSegment]:
        segments: list[ExtractedSegment] = []
        reader = PdfReader(str(file_path))

        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if len(text) >= self.min_chars_before_ocr:
                segments.append(ExtractedSegment(page=page_index, source="native", text=text))
                continue

            image_payload = self._extract_page_image(page)
            if image_payload is None:
                continue

            image_bytes, mime_type = image_payload
            ocr_text = self.ai_client.extract_text_from_image(
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
            if ocr_text:
                segments.append(ExtractedSegment(page=page_index, source="ocr", text=ocr_text))

        return segments

    def _extract_page_image(self, page) -> tuple[bytes, str] | None:
        images = getattr(page, "images", None)
        if not images:
            return None

        image_file = images[0]
        image_name = getattr(image_file, "name", "") or ""
        suffix = Path(image_name).suffix.lower()

        mime_type = "image/png"
        if suffix in {".jpg", ".jpeg"}:
            mime_type = "image/jpeg"

        data = getattr(image_file, "data", None)
        if not data:
            return None

        return data, mime_type
