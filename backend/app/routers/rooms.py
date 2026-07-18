from __future__ import annotations

import asyncio
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Room, User
from ..schemas.room import (
    AlgorithmChoice,
    OptionCreate,
    OptionPublic,
    RoomCreate,
    RoomJoin,
    RoomStart,
    RoomState,
    SessionResponse,
    UserPublic,
    VoteCreate,
    VotePublic,
)
from ..services.room_service import RoomService
from ..state_machine import Phase
from ..utils.auth import get_current_user, require_host
from ..websockets import manager

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


def _service(db: Session) -> RoomService:
    return RoomService(db)


async def _broadcast_state(code: str, service: RoomService, room: Room) -> None:
    state = service.snapshot(room)
    await manager.broadcast(code, {"type": "state", "state": state.model_dump(mode="json")})


@router.post("", response_model=SessionResponse, status_code=201)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    svc = _service(db)
    room, host = svc.create_room(payload.title, payload.algorithm.value, payload.host_name)
    state = svc.snapshot(room)
    return SessionResponse(
        session_token=host.session_token,
        user=UserPublic.model_validate(host),
        room=state,
    )


@router.post("/{code}/join", response_model=SessionResponse)
async def join_room(code: str, payload: RoomJoin, db: Session = Depends(get_db)):
    svc = _service(db)
    room, user = svc.join_room(code, payload.name)
    state = svc.snapshot(room)
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return SessionResponse(
        session_token=user.session_token,
        user=UserPublic.model_validate(user),
        room=state,
    )


@router.get("/{code}", response_model=RoomState)
def get_room(code: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.code == code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return _service(db).snapshot(room)


@router.post("/{code}/start", response_model=RoomState)
async def start_submission(
    code: str,
    payload: RoomStart,
    ctx: Tuple[User, Room] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user, room = ctx
    if room.code != code.upper():
        raise HTTPException(status_code=403, detail="Wrong room")
    require_host(user, room)
    if payload.algorithm is not None:
        room.algorithm = payload.algorithm.value
        db.commit()
    svc = _service(db)
    room = svc.transition(room, Phase.SUBMISSION)
    state = svc.snapshot(room)
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return state


@router.post("/{code}/vote-phase", response_model=RoomState)
async def start_voting(
    code: str,
    ctx: Tuple[User, Room] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user, room = ctx
    if room.code != code.upper():
        raise HTTPException(status_code=403, detail="Wrong room")
    require_host(user, room)
    svc = _service(db)
    if len(room.options) < 2:
        raise HTTPException(status_code=409, detail="Need at least 2 options to vote")
    room = svc.transition(room, Phase.VOTING)
    state = svc.snapshot(room)
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return state


@router.post("/{code}/resolve", response_model=RoomState)
async def resolve_room(
    code: str,
    ctx: Tuple[User, Room] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user, room = ctx
    if room.code != code.upper():
        raise HTTPException(status_code=403, detail="Wrong room")
    require_host(user, room)
    svc = _service(db)
    room = svc.resolve(room)
    state = svc.snapshot(room)
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return state


@router.post("/{code}/reset", response_model=RoomState)
async def reset_room(
    code: str,
    ctx: Tuple[User, Room] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user, room = ctx
    if room.code != code.upper():
        raise HTTPException(status_code=403, detail="Wrong room")
    require_host(user, room)
    svc = _service(db)
    room = svc.transition(room, Phase.LOBBY)
    state = svc.snapshot(room)
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return state


@router.post("/{code}/options", response_model=OptionPublic)
async def add_option(
    code: str,
    payload: OptionCreate,
    ctx: Tuple[User, Room] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user, room = ctx
    if room.code != code.upper():
        raise HTTPException(status_code=403, detail="Wrong room")
    svc = _service(db)
    option = svc.add_option(room, user, payload.text)
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return OptionPublic.model_validate(option)


@router.delete("/{code}/options/{option_id}")
async def delete_option(
    code: str,
    option_id: int,
    ctx: Tuple[User, Room] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user, room = ctx
    if room.code != code.upper():
        raise HTTPException(status_code=403, detail="Wrong room")
    svc = _service(db)
    svc.remove_option(room, user, option_id)
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return {"ok": True}


@router.post("/{code}/votes", response_model=VotePublic)
async def cast_vote(
    code: str,
    payload: VoteCreate,
    ctx: Tuple[User, Room] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user, room = ctx
    if room.code != code.upper():
        raise HTTPException(status_code=403, detail="Wrong room")
    svc = _service(db)
    vote = svc.cast_vote(
        room,
        user,
        payload.option_id,
        payload.kind,
        payload.is_dealbreaker,
    )
    asyncio.create_task(_broadcast_state(room.code, svc, room))
    return VotePublic.model_validate(vote)
