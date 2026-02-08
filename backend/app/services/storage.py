from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SavedFile:
    storage_path: Path
    file_size: int


class FileStorageService:
    def __init__(self, upload_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, document_id: str, filename: str, content: bytes) -> SavedFile:
        safe_name = self._sanitize_filename(filename)
        storage_name = f"{document_id}_{safe_name}"
        storage_path = self.upload_dir / storage_name
        storage_path.write_bytes(content)
        return SavedFile(storage_path=storage_path, file_size=len(content))

    def _sanitize_filename(self, filename: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", filename).strip("._")
        return cleaned or "document.bin"
