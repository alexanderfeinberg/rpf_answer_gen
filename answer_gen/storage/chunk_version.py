from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from . import Base


class ChunkVersion(Base):
    __tablename__ = "chunk_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_name = Column(String(100), nullable=False, unique=True)

    chunks = relationship("Chunk", back_populates="chunk_version")

    def to_dict(self) -> dict:
        return {"id": self.id, "version_name": self.version_name}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChunkVersion id={self.id} name={self.version_name!r}>"
