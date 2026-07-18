"""Session-token authentication.

Tokens are opaque random strings stored in the DB. They authenticate a single
user within a single room. The auth context is resolved via a dependency that
reads the Authorization header or `token` query param (for WebSocket).
"""
from __future__ import annotations

import secrets
from typing import Optional, Tuple

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Room, User


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def generate_room_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _resolve_token(authorization: Optional[str], token_query: Optional[str]) -> Optional[str]:
    if token_query:
        return token_query
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return authorization


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> Tuple[User, Room]:
    raw = _resolve_token(authorization, token)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    user = db.query(User).filter(User.session_token == raw).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    room = db.query(Room).filter(Room.id == user.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return user, room


def require_host(user: User, room: Room) -> None:
    if not user.is_host or room.host_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Host only")
