from types import SimpleNamespace

import pytest

from answer_gen.components.ingestion.document_ingestor import (
    DocumentIngestorConfig,
    DocumentIngestorWorker,
)


def _build_config() -> DocumentIngestorConfig:
    return DocumentIngestorConfig(
        max_insert_chunks=100,
        chunk_window=500,
        chunk_overlap=50,
        chunk_token_model_name="gpt-4",
        chunk_version_name="v1",
        embed_buffer_size=10,
    )


def test_dedupe_documents_filters_existing_hashes(monkeypatch):
    class _FakeChunker:
        def __init__(self, *_args, **_kwargs):
            pass

    class _FakeEmbedder:
        def encode(self, texts):
            return [[0.1] for _ in texts]

    class _FakeDoc:
        def __init__(self, hash_value):
            self.hash = hash_value

    class _FakeStore:
        def get_documents_by_hashes(self, _hashes):
            return [_FakeDoc("hash-a")]

    hash_map = {b"a": "hash-a", b"b": "hash-b"}

    monkeypatch.setattr("answer_gen.components.ingestion.document_ingestor.Chunker", _FakeChunker)
    monkeypatch.setattr("answer_gen.components.ingestion.document_ingestor.Embedder", _FakeEmbedder)
    monkeypatch.setattr(
        "answer_gen.components.ingestion.document_ingestor.get_document_hash",
        lambda payload: hash_map[payload],
    )

    worker = DocumentIngestorWorker("sqlite://", _build_config())
    docs = [("a.pdf", b"a"), ("b.pdf", b"b")]
    deduped = worker._dedupe_documents(docs, _FakeStore())

    assert deduped == [("b.pdf", b"b", "hash-b")]


def test_attach_embeddings_raises_on_vector_count_mismatch(monkeypatch):
    class _FakeChunker:
        def __init__(self, *_args, **_kwargs):
            pass

    class _FakeEmbedder:
        def encode(self, _texts):
            return [[0.1, 0.2]]

    monkeypatch.setattr("answer_gen.components.ingestion.document_ingestor.Chunker", _FakeChunker)
    monkeypatch.setattr("answer_gen.components.ingestion.document_ingestor.Embedder", _FakeEmbedder)

    worker = DocumentIngestorWorker("sqlite://", _build_config())
    chunks = [SimpleNamespace(content="c1", embedding=None), SimpleNamespace(content="c2", embedding=None)]

    with pytest.raises(RuntimeError, match="Embedding count mismatch"):
        worker._attach_embeddings(chunks)
