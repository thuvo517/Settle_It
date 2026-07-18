from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AlgorithmChoice(str, Enum):
    weighted_random = "weighted_random"
    bracket = "bracket"
    iterative_veto = "iterative_veto"


class RoomCreate(BaseModel):
    title: str = Field(default="Untitled Decision", max_length=120)
    algorithm: AlgorithmChoice = AlgorithmChoice.iterative_veto
    host_name: str = Field(..., min_length=1, max_length=40)


class RoomJoin(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)


class RoomStart(BaseModel):
    algorithm: Optional[AlgorithmChoice] = None


class UserPublic(BaseModel):
    id: int
    name: str
    is_host: bool
    is_online: bool

    class Config:
        from_attributes = True


class OptionPublic(BaseModel):
    id: int
    text: str
    author_id: int
    eliminated: bool
    weight: float

    class Config:
        from_attributes = True


class VotePublic(BaseModel):
    id: int
    user_id: int
    option_id: int
    round_number: int
    kind: str
    is_dealbreaker: bool

    class Config:
        from_attributes = True


class OptionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=160)


class VoteCreate(BaseModel):
    option_id: int
    kind: str = Field(default="eliminate")
    is_dealbreaker: bool = False


class RoomState(BaseModel):
    id: int
    code: str
    title: str
    algorithm: str
    phase: str
    host_id: Optional[int]
    phase_deadline: Optional[datetime]
    winner_option_id: Optional[int]
    users: List[UserPublic]
    options: List[OptionPublic]
    votes: List[VotePublic]
    meta: dict = {}


class SessionResponse(BaseModel):
    session_token: str
    user: UserPublic
    room: RoomState
