from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    option_id = Column(Integer, ForeignKey("options.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, default=0, nullable=False)
    kind = Column(String(16), nullable=False, default="eliminate")
    is_dealbreaker = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    room = relationship("Room", back_populates="votes")
    user = relationship("User", back_populates="votes")
    option = relationship("Option", back_populates="votes")
