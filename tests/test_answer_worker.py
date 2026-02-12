import asyncio
from types import SimpleNamespace

import pytest

import answer_gen.exceptions as exceptions
from answer_gen.components.answers.answer_worker import AnswerWorker
from answer_gen.utils.config.answer_worker_config import AnswerWorkerConfig


class _DummyContext:
    def __init__(self, session):
        self._session = session

    def __enter__(self):
        return self._session

    def __exit__(self, exc_type, exc, tb):
        return False


def _build_config() -> AnswerWorkerConfig:
    return AnswerWorkerConfig(
        embedding_model="test-model",
        embedding_batch_size=2,
        answer_prompt_path="config/answer_prompt.txt",
        answer_model="gpt-4o-mini",
        min_similarity=0.5,
        top_k=2,
        chunk_version_name="v1",
        answer_version_name="v1",
    )


def test_answer_worker_raises_for_missing_question(monkeypatch):
    class _FakeEmbedder:
        def __init__(self, *_args, **_kwargs):
            pass

    class _FakeStore:
        def get_question_by_id(self, _question_id):
            return None

    monkeypatch.setattr("answer_gen.components.answers.answer_worker.Embedder", _FakeEmbedder)
    monkeypatch.setattr("answer_gen.components.answers.answer_worker.build_connection", lambda _db_url: _DummyContext(object()))
    monkeypatch.setattr("answer_gen.components.answers.answer_worker.Persistence", lambda _session: _FakeStore())

    worker = AnswerWorker("sqlite://", generative_client=object(), config=_build_config())

    with pytest.raises(exceptions.InvalidResourceIdentifier):
        asyncio.run(worker(123))


def test_answer_worker_returns_cached_answers_without_generation(monkeypatch):
    class _FakeEmbedder:
        def __init__(self, *_args, **_kwargs):
            pass

    class _FakeAnswer:
        def to_dict(self):
            return {"id": 10, "content": "cached"}

    class _FakeQuestion:
        id = 7
        content = "What is your SLA?"
        answers = [_FakeAnswer()]

    class _FakeStore:
        def get_question_by_id(self, _question_id):
            return _FakeQuestion()

    def _should_not_be_called(*_args, **_kwargs):
        raise AssertionError("generate_single_answer should not be called for cached answers")

    monkeypatch.setattr("answer_gen.components.answers.answer_worker.Embedder", _FakeEmbedder)
    monkeypatch.setattr("answer_gen.components.answers.answer_worker.build_connection", lambda _db_url: _DummyContext(object()))
    monkeypatch.setattr("answer_gen.components.answers.answer_worker.Persistence", lambda _session: _FakeStore())
    monkeypatch.setattr("answer_gen.components.answers.answer_worker.generate_single_answer", _should_not_be_called)

    worker = AnswerWorker("sqlite://", generative_client=object(), config=_build_config())
    result = asyncio.run(worker(7))

    assert result["question"] == 7
    assert result["answers"] == [{"id": 10, "content": "cached"}]
