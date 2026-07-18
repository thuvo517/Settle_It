"""Single-elimination bracket.

Options are seeded by (eliminated=False, highest aggregate weight, lowest id).
In each round, adjacent pairs face off and the one with more "keep" votes
advances (ties fall back to "eliminate" vote differential, then seed). Byes
are inserted when the number of live options is not a power of 2.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..utils.dealbreaker import apply_dealbreakers
from .base import Algorithm, AlgorithmResult, OptionInput, VoteInput


class Bracket(Algorithm):
    name = "bracket"

    def _score_pair(
        self,
        a: int,
        b: int,
        keeps: Dict[int, int],
        eliminates: Dict[int, int],
    ) -> int:
        a_net = keeps.get(a, 0) - eliminates.get(a, 0)
        b_net = keeps.get(b, 0) - eliminates.get(b, 0)
        if a_net != b_net:
            return a if a_net > b_net else b
        if keeps.get(a, 0) != keeps.get(b, 0):
            return a if keeps[a] > keeps[b] else b
        return min(a, b)

    def run(
        self,
        options: List[OptionInput],
        votes: List[VoteInput],
        num_players: int,
        seed: Optional[int] = None,
    ) -> AlgorithmResult:
        live = [o for o in options if not o.eliminated]
        if not live:
            return AlgorithmResult(winner_id=None)

        dealbreaker_pairs = [(v.option_id, v.user_id) for v in votes if v.is_dealbreaker]
        surviving_ids = set(apply_dealbreakers([o.id for o in live], dealbreaker_pairs))
        live = [o for o in live if o.id in surviving_ids]
        if not live:
            return AlgorithmResult(winner_id=None)

        keeps: Dict[int, int] = {}
        eliminates: Dict[int, int] = {}
        for v in votes:
            if v.is_dealbreaker:
                continue
            if v.kind == "keep":
                keeps[v.option_id] = keeps.get(v.option_id, 0) + 1
            elif v.kind == "eliminate":
                eliminates[v.option_id] = eliminates.get(v.option_id, 0) + 1

        seeded = sorted(
            live,
            key=lambda o: (-(keeps.get(o.id, 0) - eliminates.get(o.id, 0)), -o.weight, o.id),
        )

        bracket: List[Optional[int]] = [o.id for o in seeded]
        eliminated_order: List[int] = []
        rounds: List[dict] = []
        round_num = 1
        while len(bracket) > 1:
            next_round: List[int] = []
            pairings: List[Tuple[Optional[int], Optional[int]]] = []
            i = 0
            while i < len(bracket):
                a = bracket[i]
                b = bracket[i + 1] if i + 1 < len(bracket) else None
                pairings.append((a, b))
                if b is None:
                    next_round.append(a)
                else:
                    winner = self._score_pair(a, b, keeps, eliminates)
                    loser = b if winner == a else a
                    eliminated_order.append(loser)
                    next_round.append(winner)
                i += 2
            rounds.append({"round": round_num, "pairings": pairings})
            bracket = next_round
            round_num += 1

        winner = bracket[0] if bracket else None
        return AlgorithmResult(
            winner_id=winner,
            eliminated_ids=eliminated_order,
            survivors=[winner] if winner else [],
            rounds=rounds,
            trace=[f"seeded={[o.id for o in seeded]}"],
        )
