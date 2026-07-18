"""High-level room operations used by routers and WebSocket handlers."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..algorithms import get_algorithm
from ..algorithms.base import OptionInput, VoteInput
from ..config import settings
from ..models import Option, Room, User, Vote
from ..schemas.room import (
    OptionPublic,
    RoomState,
    UserPublic,
    VotePublic,
)
from ..state_machine import Phase, RoomFSM
from ..utils.auth import generate_room_code, generate_token
from ..utils.fuzzy import find_duplicate, normalize


class RoomService:
    def __init__(self, db: Session):
        self.db = db

    # ---- Lifecycle ----
    def create_room(self, title: str, algorithm: str, host_name: str) -> Tuple[Room, User]:
        code = self._unique_code()
        room = Room(code=code, title=title, algorithm=algorithm, phase=Phase.LOBBY.value)
        self.db.add(room)
        self.db.flush()
        host = User(
            room_id=room.id,
            name=host_name[:40],
            session_token=generate_token(),
            is_host=True,
        )
        self.db.add(host)
        self.db.flush()
        room.host_id = host.id
        self.db.commit()
        self.db.refresh(room)
        self.db.refresh(host)
        return room, host

    def _unique_code(self) -> str:
        for _ in range(20):
            code = generate_room_code()
            exists = self.db.query(Room).filter(Room.code == code).first()
            if not exists:
                return code
        raise HTTPException(status_code=500, detail="Could not allocate room code")

    def join_room(self, code: str, name: str) -> Tuple[Room, User]:
        room = self.db.query(Room).filter(Room.code == code.upper()).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        if room.phase != Phase.LOBBY.value:
            raise HTTPException(status_code=409, detail="Room already started")
        count = self.db.query(User).filter(User.room_id == room.id).count()
        if count >= settings.max_players:
            raise HTTPException(status_code=409, detail="Room is full")
        user = User(
            room_id=room.id,
            name=name[:40],
            session_token=generate_token(),
            is_host=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(room)
        return room, user

    # ---- Transitions ----
    def transition(self, room: Room, target: Phase) -> Room:
        fsm = RoomFSM.from_str(room.phase)
        fsm.transition(target)
        room.phase = fsm.phase.value
        room.phase_started_at = datetime.utcnow()
        if target == Phase.SUBMISSION:
            room.phase_deadline = datetime.utcnow() + timedelta(seconds=settings.submission_seconds)
        elif target == Phase.VOTING:
            room.phase_deadline = datetime.utcnow() + timedelta(seconds=settings.voting_seconds)
        else:
            room.phase_deadline = None
        if target == Phase.LOBBY:
            room.winner_option_id = None
            self.db.query(Option).filter(Option.room_id == room.id).delete()
            self.db.query(Vote).filter(Vote.room_id == room.id).delete()
        self.db.commit()
        self.db.refresh(room)
        return room

    # ---- Submissions ----
    def add_option(self, room: Room, user: User, text: str) -> Option:
        if room.phase != Phase.SUBMISSION.value:
            raise HTTPException(status_code=409, detail="Not accepting submissions")
        normalized = normalize(text)
        if not normalized:
            raise HTTPException(status_code=400, detail="Empty option")

        existing = self.db.query(Option).filter(Option.room_id == room.id).all()
        dup = find_duplicate(
            normalized,
            [o.normalized_text for o in existing],
            threshold=settings.fuzzy_threshold,
        )
        if dup is not None:
            raise HTTPException(status_code=409, detail=f"Duplicate of existing option: '{dup}'")

        count_by_user = (
            self.db.query(Option)
            .filter(Option.room_id == room.id, Option.author_id == user.id)
            .count()
        )
        if count_by_user >= settings.max_options_per_player:
            raise HTTPException(status_code=409, detail="Submission limit reached")

        option = Option(
            room_id=room.id,
            author_id=user.id,
            text=text[:160],
            normalized_text=normalized[:160],
            weight=1.0,
        )
        self.db.add(option)
        self.db.commit()
        self.db.refresh(option)
        return option

    def remove_option(self, room: Room, user: User, option_id: int) -> None:
        opt = (
            self.db.query(Option)
            .filter(Option.id == option_id, Option.room_id == room.id)
            .first()
        )
        if not opt:
            raise HTTPException(status_code=404, detail="Option not found")
        if opt.author_id != user.id and not user.is_host:
            raise HTTPException(status_code=403, detail="Cannot remove others' options")
        if room.phase != Phase.SUBMISSION.value:
            raise HTTPException(status_code=409, detail="Locked")
        self.db.delete(opt)
        self.db.commit()

    # ---- Voting ----
    def cast_vote(
        self,
        room: Room,
        user: User,
        option_id: int,
        kind: str,
        is_dealbreaker: bool,
    ) -> Vote:
        if room.phase != Phase.VOTING.value:
            raise HTTPException(status_code=409, detail="Not in voting phase")
        if kind not in {"eliminate", "keep"}:
            raise HTTPException(status_code=400, detail="Invalid vote kind")
        option = (
            self.db.query(Option)
            .filter(Option.id == option_id, Option.room_id == room.id)
            .first()
        )
        if not option:
            raise HTTPException(status_code=404, detail="Option not found")

        existing = (
            self.db.query(Vote)
            .filter(
                Vote.room_id == room.id,
                Vote.user_id == user.id,
                Vote.option_id == option_id,
                Vote.round_number == 0,
            )
            .first()
        )
        if existing:
            existing.kind = kind
            existing.is_dealbreaker = is_dealbreaker
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Two concurrent requests (double-click, client retry) can both pass
        # the `existing` check above before either commits. The DB-level
        # unique constraint on (room_id, user_id, option_id, round_number)
        # guarantees only one insert wins; the loser falls back to updating
        # the row the winner just created instead of raising to the caller.
        vote = Vote(
            room_id=room.id,
            user_id=user.id,
            option_id=option_id,
            round_number=0,
            kind=kind,
            is_dealbreaker=is_dealbreaker,
        )
        self.db.add(vote)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            winner = (
                self.db.query(Vote)
                .filter(
                    Vote.room_id == room.id,
                    Vote.user_id == user.id,
                    Vote.option_id == option_id,
                    Vote.round_number == 0,
                )
                .first()
            )
            if not winner:
                # Constraint violation for some other reason - re-raise.
                raise
            winner.kind = kind
            winner.is_dealbreaker = is_dealbreaker
            self.db.commit()
            self.db.refresh(winner)
            return winner
        self.db.refresh(vote)
        return vote

    # ---- Resolve ----
    def resolve(self, room: Room, seed: Optional[int] = None) -> Room:
        if room.phase not in {Phase.VOTING.value, Phase.SUBMISSION.value}:
            raise HTTPException(status_code=409, detail="Cannot resolve from this phase")
        options = self.db.query(Option).filter(Option.room_id == room.id).all()
        votes = self.db.query(Vote).filter(Vote.room_id == room.id).all()
        num_players = self.db.query(User).filter(User.room_id == room.id).count()

        opt_inputs = [
            OptionInput(id=o.id, text=o.text, weight=o.weight, eliminated=o.eliminated)
            for o in options
        ]
        vote_inputs = [
            VoteInput(
                user_id=v.user_id,
                option_id=v.option_id,
                round_number=v.round_number,
                kind=v.kind,
                is_dealbreaker=v.is_dealbreaker,
            )
            for v in votes
        ]
        algo = get_algorithm(room.algorithm)
        result = algo.run(opt_inputs, vote_inputs, num_players, seed=seed)

        for o in options:
            o.eliminated = o.id != result.winner_id
        room.winner_option_id = result.winner_id
        room.meta = {
            "trace": result.trace,
            "rounds": result.rounds,
            "survivors": result.survivors,
        }
        fsm = RoomFSM.from_str(room.phase)
        if fsm.phase != Phase.RESULTS:
            fsm.transition(Phase.RESULTS)
            room.phase = fsm.phase.value
        room.phase_deadline = None
        self.db.commit()
        self.db.refresh(room)
        return room

    # ---- Serialization ----
    def snapshot(self, room: Room) -> RoomState:
        users = self.db.query(User).filter(User.room_id == room.id).order_by(User.id).all()
        options = (
            self.db.query(Option)
            .filter(Option.room_id == room.id)
            .order_by(Option.id)
            .all()
        )
        votes = self.db.query(Vote).filter(Vote.room_id == room.id).all()
        return RoomState(
            id=room.id,
            code=room.code,
            title=room.title,
            algorithm=room.algorithm,
            phase=room.phase,
            host_id=room.host_id,
            phase_deadline=room.phase_deadline,
            winner_option_id=room.winner_option_id,
            users=[UserPublic.model_validate(u) for u in users],
            options=[OptionPublic.model_validate(o) for o in options],
            votes=[VotePublic.model_validate(v) for v in votes],
            meta=room.meta or {},
        )
