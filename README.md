# SettleIt

An app for groups that can't decide where to eat. Everyone joins a room,
throws in options, votes, and a voting algorithm picks the winner. State
syncs live over WebSockets so everyone sees the same thing.

Built with FastAPI, React, and Postgres. Runs on Docker behind Nginx.

## How it works

A room moves through four phases: lobby, submission, voting, results. The
host controls the transitions, and a background task auto-advances a phase
if its deadline passes so a room doesn't stall when the host walks away.

There are three ways to settle a vote, picked when the room is created:

- `iterative_veto`: options get eliminated round by round. A majority of
  eliminate votes kills an option outright, otherwise the least-kept one goes.
- `bracket`: single elimination, seeded by keep votes.
- `weighted_random`: keep votes boost an option's odds, eliminate votes
  shrink them, then a seeded RNG draws the winner.

Anyone can mark an option as a dealbreaker, which removes it no matter how
the rest of the room voted (with a fallback so you can't dealbreaker your
way to zero options). Near-duplicate submissions ("pizza palace" vs
"Pizza Palace!!") get rejected with fuzzy matching.

Auth is simple: joining a room gets you a random session token that's only
valid for that room. No accounts. Every state change pushes a fresh room
snapshot to all connected clients over the WebSocket.

## Quick start

### Local dev

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

Visit http://localhost:5173.

### Run the full stack (Docker)

```bash
cp .env.example .env
docker compose up --build
# App at http://localhost/
```

### Run tests

```bash
cd backend
pytest -v
```

## Architecture

```
Browser ─┬─ GET  /            ─► Nginx ─► React SPA
         ├─ GET  /api/*       ─► Nginx ─► FastAPI
         └─ WS   /ws/rooms/.. ─► Nginx ─► FastAPI (ConnectionManager)

FastAPI ─► SQLAlchemy ─► PostgreSQL
        │
        └─► Deadline watcher (asyncio task)
```

### Project layout

```
backend/
  app/
    main.py                FastAPI app + deadline watcher
    config.py              Pydantic settings
    database.py            SQLAlchemy setup
    models/                Room, User, Option, Vote (SQLA)
    schemas/               Pydantic DTOs
    routers/rooms.py       REST API
    routers/ws.py          WebSocket endpoint
    services/room_service.py  Orchestration layer
    state_machine/fsm.py   Explicit FSM
    algorithms/            3 voting algorithms + shared base
    utils/auth.py          Session-token auth dependency
    utils/fuzzy.py         Option dedup
    utils/dealbreaker.py   Dealbreaker sweep
    websockets/manager.py  Room-scoped broadcast manager
  tests/                   unit tests
  Dockerfile
frontend/
  src/
    App.jsx
    components/            Home, Room, Lobby, Submission, Voting, Results
    hooks/                 useRoomSocket, useCountdown
    api/client.js          Fetch wrapper
  Dockerfile
  nginx-frontend.conf
nginx/nginx.conf           Reverse proxy (API + WS + SPA)
docker-compose.yml
```

## API surface (selected)

| Method | Path | Purpose |
|-------:|------|---------|
| POST   | `/api/rooms` | Create room (returns session token) |
| POST   | `/api/rooms/{code}/join` | Join lobby with display name |
| GET    | `/api/rooms/{code}` | Snapshot room state |
| POST   | `/api/rooms/{code}/start` | host: lobby → submission |
| POST   | `/api/rooms/{code}/vote-phase` | host: submission → voting |
| POST   | `/api/rooms/{code}/resolve` | host: voting → results |
| POST   | `/api/rooms/{code}/reset` | host: any → lobby |
| POST   | `/api/rooms/{code}/options` | Submit an option |
| DELETE | `/api/rooms/{code}/options/{id}` | Remove an option (author/host) |
| POST   | `/api/rooms/{code}/votes` | Cast/update a vote |
| WS     | `/ws/rooms/{code}?token=...` | Real-time state stream |
| GET    | `/api/health` | Health probe |

## Deployment (AWS EC2)

1. `scp` the repo to a t3.small (or larger) running Docker.
2. `cp .env.example .env`, set `POSTGRES_PASSWORD` and `SECRET_KEY`.
3. `docker compose up -d --build`.
4. Point a Route 53 A record at the instance; put SettleIt behind an ALB for
   TLS termination and enable the ALB → Nginx health check on `/health`.

The three Docker healthchecks (db → backend → nginx) let Compose restart
unhealthy containers automatically, and the Nginx `/health` endpoint exposes
a cheap uptime probe for external monitoring.
