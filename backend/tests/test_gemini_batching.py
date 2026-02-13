from __future__ import annotations

from backend.app.services.gemini import GeminiClient


class _Embedding:
    def __init__(self, values: list[float]) -> None:
        self.values = values


class _EmbedResponse:
    def __init__(self, embeddings: list[_Embedding]) -> None:
        self.embeddings = embeddings


class _Models:
    def __init__(self) -> None:
        self.batch_sizes: list[int] = []

    def embed_content(self, *, model: str, contents: list[str], config) -> _EmbedResponse:  # noqa: ANN001
        # Enforce the upstream API constraint in the test.
        assert len(contents) <= 100
        self.batch_sizes.append(len(contents))
        return _EmbedResponse([_Embedding([float(i)]) for i in range(len(contents))])


class _Client:
    def __init__(self) -> None:
        self.models = _Models()


def test_embed_texts_splits_large_batches() -> None:
    client = GeminiClient(
        api_key="test-key",
        model_name="gemini-test",
        embedding_model="embedding-test",
        use_system_proxy=False,
    )
    stub = _Client()
    client._client = stub  # type: ignore[attr-defined]

    texts = [f"chunk-{i}" for i in range(205)]
    vectors = client.embed_texts(texts)

    assert len(vectors) == 205
    assert stub.models.batch_sizes == [100, 100, 5]

