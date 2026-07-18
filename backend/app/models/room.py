from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(8), unique=True, index=True, nullable=False)
    title = Column(String(120), nullable=False, default="Untitled Decision")
    algorithm = Column(String(32), nullable=False, default="iterative_veto")
    phase = Column(String(32), nullable=False, default="lobby")
    host_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    phase_started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    phase_deadline = Column(DateTime, nullable=True)
    winner_option_id = Column(Integer, nullable=True)
    meta = Column(JSON, default=dict, nullable=False)

    users = relationship("User", back_populates="room", cascade="all, delete-orphan")
    options = relationship("Option", back_populates="room", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="room", cascade="all, delete-orphan")
