from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    api_prefix: str
    data_dir: Path
    upload_dir: Path
    database_path: Path
    gemini_api_key: str | None
    gemini_model: str
    pdf_min_chars_before_ocr: int

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"

    @property
    def allowed_extensions(self) -> set[str]:
        return {".pdf", ".jpg", ".jpeg", ".png"}

    @classmethod
    def from_env(cls) -> "Settings":
        root_dir = Path(__file__).resolve().parents[2]
        backend_dir = root_dir / "backend"
        data_dir = Path(os.getenv("APP_DATA_DIR", backend_dir / "data")).resolve()
        upload_dir = Path(os.getenv("APP_UPLOAD_DIR", data_dir / "uploads")).resolve()
        database_path = Path(os.getenv("APP_DB_PATH", data_dir / "app.db")).resolve()

        return cls(
            app_name=os.getenv("APP_NAME", "TUSAS Belge Analiz ve Soru-Cevap"),
            environment=os.getenv("APP_ENV", "development"),
            api_prefix="/api",
            data_dir=data_dir,
            upload_dir=upload_dir,
            database_path=database_path,
            gemini_api_key=(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            pdf_min_chars_before_ocr=int(os.getenv("PDF_MIN_CHARS_BEFORE_OCR", "40")),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
