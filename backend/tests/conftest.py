from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.tests.fakes import FakeGeminiClient, FakeVectorStore


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / "data"
    return Settings(
        app_name="TUSAS Test",
        environment="test",
        api_prefix="/api",
        data_dir=data_dir,
        upload_dir=data_dir / "uploads",
        chroma_dir=data_dir / "chroma",
        database_path=data_dir / "app.db",
        gemini_api_key="test-key",
        gemini_model="gemini-test",
        gemini_embedding_model="models/text-embedding-004",
        pdf_min_chars_before_ocr=20,
        chunk_size=220,
        chunk_overlap=40,
        retrieval_max_distance=0.5,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(
        settings=settings,
        vector_store=FakeVectorStore(),
        gemini_client=FakeGeminiClient(),
    )
    return TestClient(app)
