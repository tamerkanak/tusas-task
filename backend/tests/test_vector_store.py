from __future__ import annotations

from backend.app.services.chunking import ChunkPayload
from backend.app.services.vector_store import ChromaVectorStore


class _StubCollection:
    def __init__(self) -> None:
        self.metadatas = None

    def upsert(self, *, ids, embeddings, metadatas, documents) -> None:  # noqa: ANN001
        self.metadatas = metadatas


def test_chroma_upsert_omits_none_metadata_values() -> None:
    store = object.__new__(ChromaVectorStore)
    store.collection = _StubCollection()

    chunks = [
        ChunkPayload(
            id="c1",
            document_id="d1",
            filename="f1.pdf",
            chunk_index=0,
            page=None,
            text="hello",
        ),
        ChunkPayload(
            id="c2",
            document_id="d1",
            filename="f1.pdf",
            chunk_index=1,
            page=3,
            text="world",
        ),
    ]
    embeddings = [[0.1], [0.2]]

    store.upsert(chunks, embeddings)

    assert store.collection.metadatas is not None
    assert "page" not in store.collection.metadatas[0]
    assert store.collection.metadatas[1]["page"] == 3

