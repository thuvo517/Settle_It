# SettleIt

> Real-time group decision making. Create a room, submit options, vote, and let
> one of three algorithms settle it — synchronized across every device over
> WebSockets.

![stack](https://img.shields.io/badge/stack-FastAPI%20%C2%B7%20React%20%C2%B7%20Postgres%20%C2%B7%20Nginx%20%C2%B7%20Docker-7c5cff)

## Highlights

- **3 voting algorithms** that share a common `Algorithm` interface:
  - `iterative_veto` — majority-eliminate with low-keep fallback; deterministic.
  - `bracket` — single-elimination, keep-vote seeded, bye handling.
  - `weighted_random` — vote-modulated weights, seeded RNG for determinism.
- **Finite state machine** drives room lifecycle through 4 phases:
  `lobby → submission → voting → results` with strict illegal-transition guards.
- **Session-token auth** — opaque random tokens scoped to a single user in a
  single room; accepted via `Authorization: Bearer` or `?token=` for WebSocket.
- **Fuzzy duplicate detection** — RapidFuzz `token_set_ratio` against
  normalized text rejects near-duplicate option submissions.
- **Dealbreaker logic** — any single "⛔ dealbreaker" vote removes an option,
  with a safety fallback so the algorithm always produces a winner.
- **Real-time sync** — every state mutation rebroadcasts a full room snapshot
  to every connected client via a room-scoped `ConnectionManager`.
- **Deadline watcher** — async background task auto-advances phases when their
  deadline elapses, so sessions move even if the host goes AFK.
- **55 passing unit tests** covering algorithms, FSM, fuzzy, dealbreaker,
  auth, and the service layer edge cases.
- **One-command deploy**: `docker compose up --build`. Nginx reverse-proxies
  the React SPA, the FastAPI backend, and the WebSocket upgrade path, with
  health checks wired into every service.

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
  tests/                   55 unit tests
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
