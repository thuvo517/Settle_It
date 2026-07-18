"""Room-scoped WebSocket connection manager.

Broadcasts every phase/options/votes change to all connected clients so that
each browser renders the same synchronized room state.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import DefaultDict, Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self._user_sockets: Dict[int, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, room_code: str, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._rooms[room_code].add(ws)
            self._user_sockets[user_id] = ws

    async def disconnect(self, room_code: str, user_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self._rooms[room_code].discard(ws)
            if self._user_sockets.get(user_id) is ws:
                self._user_sockets.pop(user_id, None)

    async def broadcast(self, room_code: str, message: dict) -> None:
        data = json.dumps(message, default=str)
        stale: list[WebSocket] = []
        sockets = list(self._rooms.get(room_code, set()))
        for ws in sockets:
            try:
                await ws.send_text(data)
            except Exception:
                stale.append(ws)
        if stale:
            async with self._lock:
                for ws in stale:
                    self._rooms[room_code].discard(ws)

    def room_count(self, room_code: str) -> int:
        return len(self._rooms.get(room_code, set()))


manager = ConnectionManager()
