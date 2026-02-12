from __future__ import annotations

from dataclasses import dataclass

from answer_gen.utils.config.config_utils import read_config, get_config_str, get_config_int, get_config_float

@dataclass(frozen=True, slots=True)
class AnswerWorkerConfig:
    """Typed view over answer worker settings loaded from an INI config."""

    embedding_model: str
    embedding_batch_size: int
    answer_prompt_path: str
    answer_model: str
    min_similarity: float
    top_k: int
    chunk_version_name: str | None
    answer_version_name: str | None

    @classmethod
    def from_config(cls) -> "AnswerWorkerConfig":
        """Build an answer worker config from the currently loaded INI values."""
        embedding_model = get_config_str("embedding", "embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        embedding_batch_size = get_config_int("embedding", "embedding_batch_size", fallback=32)
        min_similarity = get_config_float("embedding", "min_similarity", fallback=0.5)

        top_k = get_config_int("database", "top_k_similar", fallback=3)
        chunk_version_name = get_config_str("chunking", "chunking_version", "v1")

        answer_prompt_path = get_config_str("answers", "answer_prompt_path", "config/answer_prompt.txt")
        answer_model = get_config_str("answers", "answer_model", "gpt-4o-mini")
        answer_version_name = get_config_str("answers", "answer_version", "v1")

        return cls(
            embedding_model=embedding_model,
            embedding_batch_size=embedding_batch_size,
            answer_prompt_path=answer_prompt_path,
            answer_model=answer_model,
            min_similarity=min_similarity,
            top_k=top_k,
            chunk_version_name=chunk_version_name,
            answer_version_name=answer_version_name,
        )


@dataclass(frozen=True, slots=True)
class BulkAnswerWorkerConfig(AnswerWorkerConfig):
    """Answer worker config variant that uses the bulk-answer prompt path."""

    @classmethod
    def from_config(cls) -> "BulkAnswerWorkerConfig":
        """Build bulk answer config from base answer config plus bulk prompt override."""
        base = AnswerWorkerConfig.from_config()
        bulk_prompt = get_config_str("answers", "bulk_answer_prompt", "config/bulk_answer_prompt.txt")
        return cls(
            embedding_model=base.embedding_model,
            embedding_batch_size=base.embedding_batch_size,
            answer_prompt_path=bulk_prompt,
            answer_model=base.answer_model,
            min_similarity=base.min_similarity,
            top_k=base.top_k,
            chunk_version_name=base.chunk_version_name,
            answer_version_name=base.answer_version_name,
        )
