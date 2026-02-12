from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func, UniqueConstraint, Index, Text
from sqlalchemy.orm import relationship

from . import Base


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        Index("uq_doc_order_version", "doc_id", "order", "chunk_version_id", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    order = Column(Integer, nullable = False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    chunk_version_id = Column(Integer, ForeignKey("chunk_versions.id"), nullable=False)

    document = relationship("Document", back_populates="chunks")
    chunk_version = relationship("ChunkVersion", back_populates="chunks")

    def to_dict(self) -> dict:
        emb = self.embedding
        if emb is None:
            emb_out = None
        elif isinstance(emb, list):
            emb_out = emb
        else:
            # pgvector may return a numpy array depending on driver/config
            tolist = getattr(emb, "tolist", None)
            emb_out = tolist() if callable(tolist) else list(emb)

        return {
            "id": self.id,
            "doc_id": self.doc_id,
            "order": self.order,
            "content": self.content,
            "embedding": emb_out,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "chunk_version_id": self.chunk_version_id,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Chunk id={self.id} doc_id={self.doc_id}>"
