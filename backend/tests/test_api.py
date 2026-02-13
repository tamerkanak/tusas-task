from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.tests.fakes import FakeGeminiClient, FakeVectorStore

SAMPLE_PDF_BASE64 = (
    "JVBERi0xLjMKJZOMi54gUmVwb3J0TGFiIEdlbmVyYXRlZCBQREYgZG9jdW1lbnQgKG9wZW5zb3VyY2UpCjEgMCBvYmoKPDwKL0YxIDIgMCBSCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9CYXNlRm9udCAvSGVsdmV0aWNhIC9FbmNvZGluZyAvV2luQW5zaUVuY29kaW5nIC9OYW1lIC9GMSAvU3VidHlwZSAvVHlwZTEgL1R5cGUgL0ZvbnQKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL0NvbnRlbnRzIDcgMCBSIC9NZWRpYUJveCBbIDAgMCA1OTUuMjc1NiA4NDEuODg5OCBdIC9QYXJlbnQgNiAwIFIgL1Jlc291cmNlcyA8PAovRm9udCAxIDAgUiAvUHJvY1NldCBbIC9QREYgL1RleHQgL0ltYWdlQiAvSW1hZ2VDIC9JbWFnZUkgXQo+PiAvUm90YXRlIDAgL1RyYW5zIDw8Cgo+PiAKICAvVHlwZSAvUGFnZQo+PgplbmRvYmoKNCAwIG9iago8PAovUGFnZU1vZGUgL1VzZU5vbmUgL1BhZ2VzIDYgMCBSIC9UeXBlIC9DYXRhbG9nCj4+CmVuZG9iago1IDAgb2JqCjw8Ci9BdXRob3IgKGFub255bW91cykgL0NyZWF0aW9uRGF0ZSAoRDoyMDI2MDIwOTAyMDgxMSswMycwMCcpIC9DcmVhdG9yIChhbm9ueW1vdXMpIC9LZXl3b3JkcyAoKSAvTW9kRGF0ZSAoRDoyMDI2MDIwOTAyMDgxMSswMycwMCcpIC9Qcm9kdWNlciAoUmVwb3J0TGFiIFBERiBMaWJyYXJ5IC0gXChvcGVuc291cmNlXCkpIAogIC9TdWJqZWN0ICh1bnNwZWNpZmllZCkgL1RpdGxlICh1bnRpdGxlZCkgL1RyYXBwZWQgL0ZhbHNlCj4+CmVuZG9iago2IDAgb2JqCjw8Ci9Db3VudCAxIC9LaWRzIFsgMyAwIFIgXSAvVHlwZSAvUGFnZXMKPj4KZW5kb2JqCjcgMCBvYmoKPDwKL0ZpbHRlciBbIC9BU0NJSTg1RGVjb2RlIC9GbGF0ZURlY29kZSBdIC9MZW5ndGggMTIxCj4+CnN0cmVhbQpHYXBRaDBFPUYsMFVcSDNUXHBOWVReUUtrP3RjPklQLDtXI1UxXjIzaWhQRU1fP0NXNEtJU2k8IVs3YCNPQl9zS09PLkNVQCJtQ2NVP3BDMDlFaUpMbSk1VmRvcCFDWmJUXTJFS29kaj4mMXJ1TSJZS2UpUFNkT34+ZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgOAowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwNjEgMDAwMDAgbiAKMDAwMDAwMDA5MiAwMDAwMCBuIAowMDAwMDAwMTk5IDAwMDAwIG4gCjAwMDAwMDA0MDIgMDAwMDAgbiAKMDAwMDAwMDQ3MCAwMDAwMCBuIAowMDAwMDAwNzMxIDAwMDAwIG4gCjAwMDAwMDA3OTAgMDAwMDAgbiAKdHJhaWxlcgo8PAovSUQgCls8NDFlNWIxZjcxNDU1ZTBiZTExOTg0NzRiNTY0MzdhNDQ+PDQxZTViMWY3MTQ1NWUwYmUxMTk4NDc0YjU2NDM3YTQ0Pl0KJSBSZXBvcnRMYWIgZ2VuZXJhdGVkIFBERiBkb2N1bWVudCAtLSBkaWdlc3QgKG9wZW5zb3VyY2UpCgovSW5mbyA1IDAgUgovUm9vdCA0IDAgUgovU2l6ZSA4Cj4+CnN0YXJ0eHJlZgoxMDAxCiUlRU9GCg=="
)


def create_pdf_bytes() -> bytes:
    return base64.b64decode(SAMPLE_PDF_BASE64)


def test_upload_accepts_supported_files_and_rejects_unsupported(client: TestClient) -> None:
    good_pdf = create_pdf_bytes()
    files = [
        ("files", ("ankara.pdf", good_pdf, "application/pdf")),
        ("files", ("not_supported.txt", b"plain text", "text/plain")),
    ]

    response = client.post("/api/documents", files=files)
    assert response.status_code == 200
    payload = response.json()

    assert len(payload["accepted_files"]) == 1
    assert len(payload["rejected_files"]) == 1
    assert payload["accepted_files"][0]["status"] == "indexed"

    list_response = client.get("/api/documents")
    assert list_response.status_code == 200
    docs = list_response.json()
    assert len(docs) == 1
    assert docs[0]["status"] == "indexed"


def test_ask_returns_grounded_answer_with_citation(client: TestClient) -> None:
    good_pdf = create_pdf_bytes()
    upload_response = client.post(
        "/api/documents",
        files=[("files", ("ankara.pdf", good_pdf, "application/pdf"))],
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_ids"][0]

    ask_response = client.post(
        "/api/questions",
        json={
            "question": "Belgede Ankara ile ilgili hangi bilgi geciyor?",
            "document_ids": [document_id],
            "top_k": 5,
        },
    )
    assert ask_response.status_code == 200
    payload = ask_response.json()

    assert payload["mode"] == "grounded_answer"
    assert payload["citations"]
    assert "Ankara" in payload["answer"]


def test_ask_returns_no_evidence_for_missing_information(client: TestClient) -> None:
    good_pdf = create_pdf_bytes()
    upload_response = client.post(
        "/api/documents",
        files=[("files", ("scope.pdf", good_pdf, "application/pdf"))],
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_ids"][0]

    ask_response = client.post(
        "/api/questions",
        json={
            "question": "Belgede Mars ussuyle ilgili bilgi var mi?",
            "document_ids": [document_id],
        },
    )
    assert ask_response.status_code == 200
    payload = ask_response.json()

    assert payload["mode"] == "no_evidence"
    assert payload["citations"] == []
    assert payload["answer"] == "Bu bilgi belgede bulunamadi."


def test_missing_api_key_fails_fast_on_upload(tmp_path) -> None:
    data_dir = tmp_path / "no_key"
    settings = Settings(
        app_name="NoKey",
        environment="test",
        api_prefix="/api",
        data_dir=data_dir,
        upload_dir=data_dir / "uploads",
        chroma_dir=data_dir / "chroma",
        database_path=data_dir / "app.db",
        gemini_api_key=None,
        gemini_model="gemini-test",
        gemini_embedding_model="models/text-embedding-004",
        gemini_use_system_proxy=False,
        pdf_min_chars_before_ocr=20,
        chunk_size=220,
        chunk_overlap=40,
        retrieval_max_distance=0.5,
        max_files_per_request=10,
        max_upload_file_size_bytes=50 * 1024 * 1024,
    )

    app = create_app(settings=settings, vector_store=FakeVectorStore())
    client = TestClient(app)

    good_pdf = create_pdf_bytes()
    response = client.post(
        "/api/documents",
        files=[("files", ("deneme.pdf", good_pdf, "application/pdf"))],
    )

    assert response.status_code == 503
    assert "API_KEY" in response.json()["detail"].upper()


def test_upload_indexes_short_native_pdf_text_even_when_ocr_threshold_high(tmp_path) -> None:
    data_dir = tmp_path / "short_native"
    settings = Settings(
        app_name="ShortNative",
        environment="test",
        api_prefix="/api",
        data_dir=data_dir,
        upload_dir=data_dir / "uploads",
        chroma_dir=data_dir / "chroma",
        database_path=data_dir / "app.db",
        gemini_api_key="test-key",
        gemini_model="gemini-test",
        gemini_embedding_model="models/text-embedding-004",
        gemini_use_system_proxy=False,
        pdf_min_chars_before_ocr=10_000,
        chunk_size=220,
        chunk_overlap=40,
        retrieval_max_distance=0.5,
        max_files_per_request=10,
        max_upload_file_size_bytes=50 * 1024 * 1024,
    )

    app = create_app(
        settings=settings,
        vector_store=FakeVectorStore(),
        gemini_client=FakeGeminiClient(),
    )
    client = TestClient(app)

    good_pdf = create_pdf_bytes()
    upload_response = client.post(
        "/api/documents",
        files=[("files", ("ankara.pdf", good_pdf, "application/pdf"))],
    )
    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["accepted_files"]
    assert payload["accepted_files"][0]["status"] == "indexed"


def test_root_serves_static_ui(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "TUSAS Case Study MVP" in response.text


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files=[("files", ("empty.pdf", b"", "application/pdf"))],
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["accepted_files"] == []
    assert payload["rejected_files"]
    assert payload["rejected_files"][0]["filename"] == "empty.pdf"
    assert payload["rejected_files"][0]["reason"] == "Dosya bos"


def test_upload_rejects_too_many_files(client: TestClient, settings: Settings) -> None:
    good_pdf = create_pdf_bytes()
    files = [
        ("files", (f"doc-{i}.pdf", good_pdf, "application/pdf"))
        for i in range(settings.max_files_per_request + 1)
    ]

    response = client.post("/api/documents", files=files)
    assert response.status_code == 400
    assert str(settings.max_files_per_request) in response.json()["detail"]


def test_upload_rejects_too_large_file(tmp_path) -> None:
    data_dir = tmp_path / "size_limit"
    settings = Settings(
        app_name="SizeLimit",
        environment="test",
        api_prefix="/api",
        data_dir=data_dir,
        upload_dir=data_dir / "uploads",
        chroma_dir=data_dir / "chroma",
        database_path=data_dir / "app.db",
        gemini_api_key="test-key",
        gemini_model="gemini-test",
        gemini_embedding_model="models/text-embedding-004",
        gemini_use_system_proxy=False,
        pdf_min_chars_before_ocr=20,
        chunk_size=220,
        chunk_overlap=40,
        retrieval_max_distance=0.5,
        max_files_per_request=10,
        max_upload_file_size_bytes=100,
    )

    app = create_app(
        settings=settings,
        vector_store=FakeVectorStore(),
        gemini_client=FakeGeminiClient(),
    )
    client = TestClient(app)

    good_pdf = create_pdf_bytes()
    response = client.post(
        "/api/documents",
        files=[("files", ("ankara.pdf", good_pdf, "application/pdf"))],
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["accepted_files"] == []
    assert payload["rejected_files"]
    assert "cok buyuk" in payload["rejected_files"][0]["reason"].lower()


def test_ask_ignores_invalid_document_ids(client: TestClient) -> None:
    good_pdf = create_pdf_bytes()
    upload_response = client.post(
        "/api/documents",
        files=[("files", ("ankara.pdf", good_pdf, "application/pdf"))],
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_ids"][0]

    ask_response = client.post(
        "/api/questions",
        json={
            "question": "Belgede Ankara ile ilgili hangi bilgi geciyor?",
            "document_ids": [document_id, "does-not-exist"],
            "top_k": 5,
        },
    )
    assert ask_response.status_code == 200
    payload = ask_response.json()

    assert payload["mode"] == "grounded_answer"
    assert payload["citations"]
    assert "Ankara" in payload["answer"]
