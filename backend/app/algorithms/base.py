from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OptionInput:
    id: int
    text: str
    weight: float = 1.0
    eliminated: bool = False


@dataclass
class VoteInput:
    user_id: int
    option_id: int
    round_number: int = 0
    kind: str = "eliminate"  # "eliminate" | "keep" | "dealbreaker"
    is_dealbreaker: bool = False


@dataclass
class AlgorithmResult:
    winner_id: Optional[int]
    eliminated_ids: List[int] = field(default_factory=list)
    survivors: List[int] = field(default_factory=list)
    rounds: List[dict] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)


class Algorithm:
    name: str = "base"

    def run(
        self,
        options: List[OptionInput],
        votes: List[VoteInput],
        num_players: int,
        seed: Optional[int] = None,
    ) -> AlgorithmResult:  # pragma: no cover - interface only
        raise NotImplementedError
