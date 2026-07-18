from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Room
from .routers import rooms as rooms_router
from .routers import ws as ws_router
from .services.room_service import RoomService
from .state_machine import Phase
from .websockets import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(_deadline_watcher())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def _deadline_watcher() -> None:
    """Advance rooms whose phase deadline has passed."""
    while True:
        try:
            await asyncio.sleep(1.0)
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                rooms = (
                    db.query(Room)
                    .filter(Room.phase_deadline.isnot(None), Room.phase_deadline <= now)
                    .all()
                )
                for room in rooms:
                    svc = RoomService(db)
                    if room.phase == Phase.SUBMISSION.value and len(room.options) >= 2:
                        svc.transition(room, Phase.VOTING)
                        await manager.broadcast(
                            room.code,
                            {
                                "type": "state",
                                "state": svc.snapshot(room).model_dump(mode="json"),
                            },
                        )
                    elif room.phase == Phase.VOTING.value:
                        svc.resolve(room)
                        await manager.broadcast(
                            room.code,
                            {
                                "type": "state",
                                "state": svc.snapshot(room).model_dump(mode="json"),
                            },
                        )
                    else:
                        # Nothing we can do automatically; clear the deadline so
                        # we stop re-processing this row.
                        room.phase_deadline = None
                        db.commit()
            finally:
                db.close()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            # Never let the watcher die
            await asyncio.sleep(1.0)


app = FastAPI(title="SettleIt", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms_router.router)
app.include_router(ws_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "settleit", "time": datetime.utcnow().isoformat()}


@app.get("/")
async def root():
    return {"name": "SettleIt API", "docs": "/docs", "health": "/api/health"}
