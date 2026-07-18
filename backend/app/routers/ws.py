from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Room, User
from ..services.room_service import RoomService
from ..websockets import manager

router = APIRouter()


def _ws_db() -> Session:
    return SessionLocal()


@router.websocket("/ws/rooms/{code}")
async def room_socket(
    websocket: WebSocket,
    code: str,
    token: str = Query(...),
):
    code = code.upper()
    db = _ws_db()
    try:
        user = db.query(User).filter(User.session_token == token).first()
        if not user:
            await websocket.close(code=4401)
            return
        room = db.query(Room).filter(Room.id == user.room_id).first()
        if not room or room.code != code:
            await websocket.close(code=4403)
            return

        await manager.connect(code, user.id, websocket)
        user.is_online = True
        db.commit()

        # Initial snapshot
        svc = RoomService(db)
        state = svc.snapshot(room)
        await websocket.send_text(
            json.dumps({"type": "state", "state": state.model_dump(mode="json")}, default=str)
        )
        await manager.broadcast(
            code,
            {"type": "presence", "user_id": user.id, "online": True},
        )

        try:
            while True:
                msg = await websocket.receive_text()
                try:
                    payload = json.loads(msg)
                except Exception:
                    payload = {"type": "unknown", "raw": msg}
                if payload.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
        except WebSocketDisconnect:
            pass
        finally:
            await manager.disconnect(code, user.id, websocket)
            # Reload user — original session may be mid-commit
            fresh = db.query(User).filter(User.id == user.id).first()
            if fresh:
                fresh.is_online = False
                db.commit()
            await manager.broadcast(
                code,
                {"type": "presence", "user_id": user.id, "online": False},
            )
    finally:
        db.close()
