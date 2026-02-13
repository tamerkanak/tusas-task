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
    chroma_dir: Path
    database_path: Path
    gemini_api_key: str | None
    gemini_model: str
    gemini_embedding_model: str
    gemini_use_system_proxy: bool
    pdf_min_chars_before_ocr: int
    chunk_size: int
    chunk_overlap: int
    retrieval_max_distance: float

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"

    @property
    def allowed_extensions(self) -> set[str]:
        return {".pdf", ".jpg", ".jpeg", ".png"}

    @classmethod
    def from_env(cls) -> "Settings":
        root_dir = Path(__file__).resolve().parents[2]
        _load_dotenv(root_dir / ".env")
        backend_dir = root_dir / "backend"
        data_dir = Path(os.getenv("APP_DATA_DIR", backend_dir / "data")).resolve()
        upload_dir = Path(os.getenv("APP_UPLOAD_DIR", data_dir / "uploads")).resolve()
        chroma_dir = Path(os.getenv("APP_CHROMA_DIR", data_dir / "chroma")).resolve()
        database_path = Path(os.getenv("APP_DB_PATH", data_dir / "app.db")).resolve()

        return cls(
            app_name=os.getenv("APP_NAME", "TUSAS Belge Analiz ve Soru-Cevap"),
            environment=os.getenv("APP_ENV", "development"),
            api_prefix="/api",
            data_dir=data_dir,
            upload_dir=upload_dir,
            chroma_dir=chroma_dir,
            database_path=database_path,
            gemini_api_key=(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
            gemini_embedding_model=os.getenv(
                "GEMINI_EMBED_MODEL", "gemini-embedding-001"
            ),
            gemini_use_system_proxy=_read_bool(
                os.getenv("GEMINI_USE_SYSTEM_PROXY"),
                default=False,
            ),
            pdf_min_chars_before_ocr=int(os.getenv("PDF_MIN_CHARS_BEFORE_OCR", "40")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "180")),
            retrieval_max_distance=float(os.getenv("RETRIEVAL_MAX_DISTANCE", "0.45")),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


def _read_bool(raw_value: str | None, *, default: bool) -> bool:
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _load_dotenv(dotenv_path: Path) -> None:
    """Load key=value pairs from .env into process environment.

    - Does not overwrite already-set environment variables.
    - No external dependency (python-dotenv) needed.
    """
    try:
        if not dotenv_path.exists():
            return
        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue

            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]

            os.environ[key] = value
    except Exception:
        # If loading fails, keep running with whatever is already in the environment.
        return
