from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .extraction import ExtractedSegment


@dataclass
class ChunkPayload:
    id: str
    document_id: str
    filename: str
    chunk_index: int
    page: int | None
    text: str


class ChunkBuilder:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 180) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap, chunk_size degerinden kucuk olmali")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def build(
        self,
        *,
        document_id: str,
        filename: str,
        segments: list[ExtractedSegment],
    ) -> list[ChunkPayload]:
        chunks: list[ChunkPayload] = []
        chunk_index = 0

        for segment in segments:
            for text_piece in self._split_text(segment.text):
                chunks.append(
                    ChunkPayload(
                        id=uuid4().hex,
                        document_id=document_id,
                        filename=filename,
                        chunk_index=chunk_index,
                        page=segment.page,
                        text=text_piece,
                    )
                )
                chunk_index += 1

        return chunks

    def _split_text(self, text: str) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        parts: list[str] = []
        start = 0
        text_len = len(normalized)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            if end < text_len:
                breakpoint_index = normalized.rfind(" ", start, end)
                if breakpoint_index > start + (self.chunk_size // 2):
                    end = breakpoint_index

            piece = normalized[start:end].strip()
            if piece:
                parts.append(piece)

            if end >= text_len:
                break

            start = max(0, end - self.chunk_overlap)

        return parts
