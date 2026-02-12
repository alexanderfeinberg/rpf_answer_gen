from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from . import Base


class AnswerVersion(Base):
    __tablename__ = "answer_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_name = Column(String(100), nullable=False, unique=True)

    answers = relationship("Answer", back_populates="answer_version")

    def to_dict(self) -> dict:
        return {"id": self.id, "version_name": self.version_name}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AnswerVersion id={self.id} name={self.version_name!r}>"
