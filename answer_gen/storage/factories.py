"""Small factory helpers for building SQLAlchemy model instances."""

from datetime import datetime
from typing import Optional

from . import (
    Document,
    ChunkVersion,
    AnswerVersion,
    Chunk,
    RFP,
    Question,
    Answer,
)


def document_factory(
    filename: str,
    storage_url: str,
    hash_value: str,
    uploaded_at: Optional[datetime] = None,
) -> Document:
    return Document(
        filename=filename,
        storage_url=storage_url,
        hash=hash_value,
        uploaded_at=uploaded_at or datetime.utcnow(),
    )


def chunk_version_factory(version_name: str) -> ChunkVersion:
    return ChunkVersion(version_name=version_name)


def answer_version_factory(version_name: str) -> AnswerVersion:
    return AnswerVersion(version_name=version_name)


def chunk_factory(
    doc_id: int,
    content: str,
    chunk_version_id: int,
    order: int,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
) -> Chunk:
    return Chunk(
        doc_id=doc_id,
        content=content,
        chunk_version_id=chunk_version_id,
        order=order,
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at or datetime.utcnow(),
    )


def rfp_factory(
    filename: str,
    storage_url: str,
    hash_value: str,
    uploaded_at: Optional[datetime] = None,
) -> RFP:
    return RFP(
        filename=filename,
        storage_url=storage_url,
        hash=hash_value,
        uploaded_at=uploaded_at or datetime.utcnow(),
    )


def question_factory(
    content: str,
    rfp_id: int,
    created_at: Optional[datetime] = None,
) -> Question:
    return Question(
        content=content,
        rfp_id=rfp_id,
        created_at=created_at or datetime.utcnow(),
    )


def answer_factory(
    content: str,
    question_id: int,
    answer_version_id: Optional[int] = None,
    created_at: Optional[datetime] = None,
) -> Answer:
    return Answer(
        content=content,
        question_id=question_id,
        answer_version_id=answer_version_id,
        created_at=created_at or datetime.utcnow(),
    )
