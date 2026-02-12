from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from . import Base


class RFP(Base):
    __tablename__ = "rfps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())
    storage_url = Column(String(500), nullable=False, unique=True)
    hash = Column(String(32), nullable=False, unique=True)

    questions = relationship("Question", back_populates="rfp", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "storage_url": self.storage_url,
            "hash": self.hash,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RFP id={self.id} filename={self.filename!r}>"
