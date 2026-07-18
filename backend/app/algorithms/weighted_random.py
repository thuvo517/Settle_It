"""Weighted random elimination.

Each option's weight starts at 1.0 and is modified by votes:
  * eliminate vote: weight *= 0.5
  * keep vote:      weight *= 1.25
  * dealbreaker:    option is removed outright

At the end we pick the single surviving option with the highest weight; ties
are broken by weighted random choice seeded by ``seed`` for determinism in
tests.
"""
from __future__ import annotations

import random
from typing import List, Optional

from ..utils.dealbreaker import apply_dealbreakers
from .base import Algorithm, AlgorithmResult, OptionInput, VoteInput


class WeightedRandom(Algorithm):
    name = "weighted_random"

    def run(
        self,
        options: List[OptionInput],
        votes: List[VoteInput],
        num_players: int,
        seed: Optional[int] = None,
    ) -> AlgorithmResult:
        rng = random.Random(seed)
        live = [o for o in options if not o.eliminated]
        if not live:
            return AlgorithmResult(winner_id=None)

        weights = {o.id: max(o.weight, 0.01) for o in live}
        trace: List[str] = []

        for v in votes:
            if v.option_id not in weights:
                continue
            if v.is_dealbreaker:
                continue  # handled in sweep
            if v.kind == "eliminate":
                weights[v.option_id] *= 0.5
            elif v.kind == "keep":
                weights[v.option_id] *= 1.25

        dealbreaker_pairs = [(v.option_id, v.user_id) for v in votes if v.is_dealbreaker]
        survivors_ids = apply_dealbreakers([o.id for o in live], dealbreaker_pairs)
        trace.append(f"dealbreaker survivors: {survivors_ids}")

        candidates = [oid for oid in survivors_ids if oid in weights]
        if not candidates:
            return AlgorithmResult(winner_id=None, eliminated_ids=[o.id for o in live])

        max_w = max(weights[c] for c in candidates)
        top = [c for c in candidates if weights[c] == max_w]
        if len(top) == 1:
            winner = top[0]
        else:
            total = sum(weights[c] for c in top)
            pick = rng.uniform(0, total)
            acc = 0.0
            winner = top[-1]
            for c in top:
                acc += weights[c]
                if pick <= acc:
                    winner = c
                    break

        eliminated = [o.id for o in live if o.id != winner]
        trace.append(f"winner={winner} weights={weights}")
        return AlgorithmResult(
            winner_id=winner,
            eliminated_ids=eliminated,
            survivors=[winner],
            trace=trace,
        )
