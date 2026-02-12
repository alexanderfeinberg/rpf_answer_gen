from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from answer_gen.exceptions import StorageWriteError
from answer_gen.storage import (
    Document,
    Chunk,
    RFP,
    Question,
    Answer,
    ChunkVersion,
    AnswerVersion,
)

logger = logging.getLogger(__name__)


class Persistence:
    """Single facade for common DB operations used by workers."""

    def __init__(self, session):
        self.session = session

    # ---- Documents ----
    def get_documents_by_hashes(self, doc_hashes: list[str]) -> list[Document]:
        if not doc_hashes:
            return []
        stmt = select(Document).where(Document.hash.in_(doc_hashes))
        return list(self.session.execute(stmt).scalars().all())

    def get_most_recent_document(self) -> Document | None:
        stmt = select(Document).order_by(Document.uploaded_at.desc()).limit(1)
        return self.session.execute(stmt).scalars().first()

    def insert_document(self, document: Document) -> None:
        self.session.add(document)

    def delete_document(self, document: Document) -> None:
        self.session.delete(document)

    # ---- RFPs ----
    def get_rfp_by_hash(self, doc_hash: str) -> RFP | None:
        stmt = select(RFP).where(RFP.hash == doc_hash)
        return self.session.execute(stmt).scalar_one_or_none()

    def insert_rfp(self, rfp: RFP) -> None:
        self.session.add(rfp)

    # ---- Questions ----
    def get_question_by_id(self, question_id: int) -> Question | None:
        stmt = select(Question).where(Question.id == question_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_questions_by_rfp(self, rfp_id: int) -> list[Question]:
        stmt = select(Question).where(Question.rfp_id == rfp_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_questions_with_answers(self, rfp_id: int) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.rfp_id == rfp_id)
            .options(selectinload(Question.answers))
        )
        return list(self.session.execute(stmt).scalars().all())

    def delete_questions_not_in(self, rfp_id: int, keep_texts: list[str]) -> int:
        if keep_texts:
            stmt = Question.__table__.delete().where(Question.rfp_id == rfp_id, ~Question.content.in_(keep_texts))
        else:
            stmt = Question.__table__.delete().where(Question.rfp_id == rfp_id)
        result = self.session.execute(stmt)
        return int(result.rowcount or 0)

    def bulk_insert_questions(self, questions: list[Question]) -> None:
        if questions:
            self.session.bulk_save_objects(questions, return_defaults = True)

    # ---- Answers ----
    def insert_answer(self, answer: Answer) -> None:
        self.session.add(answer)

    def get_answer_by_id(self, answer_id: int) -> Answer | None:
        stmt = select(Answer).where(Answer.id == answer_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def bulk_insert_answers(self, answers: list[Answer]) -> None:
        if answers:
            self.session.bulk_save_objects(answers)

    def get_answer_version_by_name(self, version_name: str) -> AnswerVersion | None:
        stmt = select(AnswerVersion).where(AnswerVersion.version_name == version_name)
        return self.session.execute(stmt).scalar_one_or_none()

    # ---- Chunks ----
    def bulk_insert_chunks(self, chunks: list[Chunk]) -> None:
        if chunks:
            self.session.bulk_save_objects(chunks)

    def get_chunks_by_doc_and_version(self, doc_id: int, chunk_version_id: int) -> list[Chunk]:
        stmt = (
            select(Chunk)
            .where(Chunk.doc_id == doc_id, Chunk.chunk_version_id == chunk_version_id)
            .order_by(Chunk.order.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_chunk_version(self, version_name: str) -> ChunkVersion | None:
        stmt = select(ChunkVersion).where(ChunkVersion.version_name == version_name)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_chunk_version_by_name(self, version_name: str) -> ChunkVersion | None:
        return self.get_chunk_version(version_name)

    def get_most_similar_chunks(
        self,
        query_embedding: list[float],
        min_similarity: float,
        top_k: int,
        chunk_version_name: str | None = None,
    ) -> Chunk | None:
        if not query_embedding:
            raise ValueError("query_embedding must be non-empty")
        distance = Chunk.embedding.cosine_distance(query_embedding)
        similarity = (1 - distance).label("similarity")

        stmt = select(Chunk).where(Chunk.embedding.isnot(None), similarity >= min_similarity)
        if chunk_version_name is not None:
            stmt = (
                stmt.join(ChunkVersion, Chunk.chunk_version_id == ChunkVersion.id)
                .where(ChunkVersion.version_name == chunk_version_name)
            )

        stmt = stmt.order_by(distance.asc()).limit(top_k)
        return self.session.execute(stmt).scalars()

    # ---- Tx helpers ----
    def flush(self) -> None:
        try:
            self.session.flush()
        except Exception:
            logger.exception("Storage flush failed")
            self.rollback()
            raise StorageWriteError(f'Unable to flush to storage.')

    def commit(self) -> None:
        try:
            self.session.commit()
        except Exception:
            logger.exception("Storage commit failed")
            self.rollback()
            raise StorageWriteError(f'Unable to commit transactiom to storage.')

    def rollback(self) -> None:
        try:
            self.session.rollback()
        except Exception:
            logger.exception("Storage rollback failed")
            raise
