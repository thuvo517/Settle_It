"""Finite state machine for a room's lifecycle.

Phases
------
LOBBY      -> players join, host sets algorithm
SUBMISSION -> each player submits options (dedup + cap enforced)
VOTING     -> players vote to eliminate, dealbreaker supported
RESULTS    -> winner selected, room frozen

Transitions are strict: illegal moves raise ``IllegalTransition``. The host
drives transitions explicitly, but SUBMISSION -> VOTING and VOTING -> RESULTS
can also be auto-triggered by the deadline watcher.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet


class Phase(str, Enum):
    LOBBY = "lobby"
    SUBMISSION = "submission"
    VOTING = "voting"
    RESULTS = "results"


class IllegalTransition(Exception):
    def __init__(self, src: Phase, dst: Phase):
        super().__init__(f"Illegal transition: {src.value} -> {dst.value}")
        self.src = src
        self.dst = dst


_ALLOWED: Dict[Phase, FrozenSet[Phase]] = {
    Phase.LOBBY: frozenset({Phase.SUBMISSION}),
    Phase.SUBMISSION: frozenset({Phase.VOTING, Phase.LOBBY}),
    Phase.VOTING: frozenset({Phase.RESULTS, Phase.VOTING, Phase.LOBBY}),
    Phase.RESULTS: frozenset({Phase.LOBBY}),
}


@dataclass
class RoomFSM:
    phase: Phase = Phase.LOBBY

    def can(self, target: Phase) -> bool:
        return target in _ALLOWED[self.phase]

    def transition(self, target: Phase) -> None:
        if not self.can(target):
            raise IllegalTransition(self.phase, target)
        self.phase = target

    @staticmethod
    def from_str(value: str) -> "RoomFSM":
        return RoomFSM(Phase(value))
