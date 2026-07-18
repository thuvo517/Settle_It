from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(160), nullable=False)
    normalized_text = Column(String(160), nullable=False, index=True)
    eliminated = Column(Boolean, default=False, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    room = relationship("Room", back_populates="options")
    author = relationship("User", back_populates="options")
    votes = relationship("Vote", back_populates="option", cascade="all, delete-orphan")
