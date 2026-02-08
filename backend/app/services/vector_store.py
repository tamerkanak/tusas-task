from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .chunking import ChunkPayload


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page: int | None
    text: str
    distance: float


class VectorStoreProtocol(Protocol):
    def upsert(self, chunks: list[ChunkPayload], embeddings: list[list[float]]) -> None: ...

    def query(
        self,
        query_embedding: list[float],
        document_ids: list[str],
        top_k: int,
    ) -> list[RetrievedChunk]: ...

    def ping(self) -> bool: ...


class ChromaVectorStore:
    def __init__(self, persist_dir: Path, collection_name: str = "document_chunks") -> None:
        import chromadb

        self.client: Any = chromadb.PersistentClient(path=str(persist_dir))
        self.collection: Any = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[ChunkPayload], embeddings: list[list[float]]) -> None:
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise ValueError("Chunk sayisi ile embedding sayisi esit olmali")

        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
            documents=[chunk.text for chunk in chunks],
        )

    def query(
        self,
        query_embedding: list[float],
        document_ids: list[str],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not document_ids:
            return []

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": {"$in": document_ids}},
            include=["metadatas", "documents", "distances"],
        )

        metadatas = result.get("metadatas", [[]])[0]
        documents = result.get("documents", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        chunks: list[RetrievedChunk] = []
        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            text = documents[index] if index < len(documents) else ""
            distance = distances[index] if index < len(distances) else 1.0

            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=str(metadata.get("document_id", "")),
                    filename=str(metadata.get("filename", "")),
                    page=metadata.get("page"),
                    text=text,
                    distance=float(distance),
                )
            )

        return chunks

    def ping(self) -> bool:
        try:
            self.collection.count()
            return True
        except Exception:
            return False


class UnavailableVectorStore:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def upsert(self, chunks: list[ChunkPayload], embeddings: list[list[float]]) -> None:
        raise RuntimeError(self.reason)

    def query(
        self,
        query_embedding: list[float],
        document_ids: list[str],
        top_k: int,
    ) -> list[RetrievedChunk]:
        raise RuntimeError(self.reason)

    def ping(self) -> bool:
        return False
