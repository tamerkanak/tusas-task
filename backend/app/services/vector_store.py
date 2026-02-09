from __future__ import annotations

import json
import math
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


class LocalJsonVectorStore:
    def __init__(self, persist_path: Path) -> None:
        self.persist_path = persist_path
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, dict[str, Any]] = {}
        self._load()

    def upsert(self, chunks: list[ChunkPayload], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk sayisi ile embedding sayisi esit olmali")

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self._records[chunk.id] = {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "page": chunk.page,
                "text": chunk.text,
                "embedding": embedding,
            }

        self._save()

    def query(
        self,
        query_embedding: list[float],
        document_ids: list[str],
        top_k: int,
    ) -> list[RetrievedChunk]:
        scored: list[tuple[float, dict[str, Any]]] = []
        allowed = set(document_ids)

        for payload in self._records.values():
            if payload.get("document_id") not in allowed:
                continue
            embedding = payload.get("embedding")
            if not isinstance(embedding, list) or not embedding:
                continue

            distance = self._cosine_distance(query_embedding, embedding)
            scored.append((distance, payload))

        scored.sort(key=lambda item: item[0])

        result: list[RetrievedChunk] = []
        for distance, payload in scored[:top_k]:
            result.append(
                RetrievedChunk(
                    chunk_id=str(payload.get("chunk_id", "")),
                    document_id=str(payload.get("document_id", "")),
                    filename=str(payload.get("filename", "")),
                    page=payload.get("page"),
                    text=str(payload.get("text", "")),
                    distance=distance,
                )
            )
        return result

    def ping(self) -> bool:
        return True

    def _cosine_distance(self, left: list[float], right: list[float]) -> float:
        length = min(len(left), len(right))
        if length == 0:
            return 1.0

        dot = sum(left[i] * right[i] for i in range(length))
        left_norm = math.sqrt(sum(left[i] * left[i] for i in range(length)))
        right_norm = math.sqrt(sum(right[i] * right[i] for i in range(length)))
        if left_norm == 0 or right_norm == 0:
            return 1.0

        similarity = dot / (left_norm * right_norm)
        return max(0.0, min(2.0, 1.0 - similarity))

    def _load(self) -> None:
        if not self.persist_path.exists():
            self._records = {}
            return

        try:
            loaded = json.loads(self.persist_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self._records = loaded
            else:
                self._records = {}
        except Exception:
            self._records = {}

    def _save(self) -> None:
        self.persist_path.write_text(
            json.dumps(self._records, ensure_ascii=False),
            encoding="utf-8",
        )


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
