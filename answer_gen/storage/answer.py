from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from . import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(600), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_version_id = Column(Integer, ForeignKey("answer_versions.id"), nullable=True)

    question = relationship("Question", back_populates="answers")
    answer_version = relationship("AnswerVersion", back_populates="answers")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "question_id": self.question_id,
            "answer_version_id": self.answer_version_id,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Answer id={self.id} question_id={self.question_id}>"
