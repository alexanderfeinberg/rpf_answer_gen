"""SQLAlchemy base and model exports for storage package."""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models so Base.metadata is populated on import
from .document import Document  # noqa: E402,F401
from .chunk_version import ChunkVersion  # noqa: E402,F401
from .answer_version import AnswerVersion  # noqa: E402,F401
from .chunk import Chunk  # noqa: E402,F401
from .rfp import RFP  # noqa: E402,F401
from .question import Question  # noqa: E402,F401
from .answer import Answer  # noqa: E402,F401
from .factories import (  # noqa: E402,F401
    document_factory,
    chunk_version_factory,
    answer_version_factory,
    chunk_factory,
    rfp_factory,
    question_factory,
    answer_factory,
)

__all__ = [
    "Base",
    "Document",
    "ChunkVersion",
    "AnswerVersion",
    "Chunk",
    "RFP",
    "Question",
    "Answer",
    "document_factory",
    "chunk_version_factory",
    "answer_version_factory",
    "chunk_factory",
    "rfp_factory",
    "question_factory",
    "answer_factory",
]
