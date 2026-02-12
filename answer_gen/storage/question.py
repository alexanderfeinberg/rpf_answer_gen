from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func, UniqueConstraint
from sqlalchemy.orm import relationship

from . import Base


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("content", "rfp_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(600), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    rfp_id = Column(Integer, ForeignKey("rfps.id"), nullable=False)

    # TODO: add question versoining

    rfp = relationship("RFP", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "rfp_id": self.rfp_id,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Question id={self.id} rfp_id={self.rfp_id}>"
