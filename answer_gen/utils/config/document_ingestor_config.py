from __future__ import annotations

from dataclasses import dataclass

from answer_gen.utils.config.config_utils import read_config, get_config_str, get_config_int


@dataclass(frozen=True, slots=True)
class DocumentIngestorConfig:
    """Typed configuration container for `DocumentIngestorWorker` settings."""

    max_insert_chunks: int
    chunk_window: int
    chunk_overlap: int
    chunk_token_model_name: str
    chunk_version_name: str
    embed_buffer_size: int | None

    @classmethod
    def from_config(cls, config_path: str = "config/global.ini") -> "DocumentIngestorConfig":
        """Build document ingestor config values from the configured INI file."""
        read_config(config_path)
        embed_buffer_size = get_config_int("embedding", "embed_buffer_size", fallback=0) or None

        return cls(
            max_insert_chunks=get_config_int("database", "max_document_insert_chunks", fallback=10000),
            chunk_window=get_config_int("chunking", "chunk_window", fallback=500),
            chunk_overlap=get_config_int("chunking", "chunk_overlap", fallback=50),
            chunk_token_model_name=get_config_str("chunking", "chunk_token_model_name", "gpt-4"),
            chunk_version_name=get_config_str("chunking", "chunking_version", "v1"),
            embed_buffer_size=get_config_int("chunking", "embed_buffer_size", fallback=512),
        )
