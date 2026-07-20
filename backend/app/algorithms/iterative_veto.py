"""Iterative veto.

Repeat until only one option survives:
  1. Sweep dealbreakers — any option with an active dealbreaker is eliminated.
  2. If a majority (> num_players/2) of voters cast an eliminate vote on any
     option, remove the option(s) with the highest eliminate count (ties: all).
  3. If no majority is reached, remove the option with the LOWEST "keep" vote
     count, breaking ties by lowest id, so the process strictly converges.

The algorithm is deterministic and suitable for synchronous replay.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import DefaultDict, Dict, List, Optional, Set, Tuple

from ..utils.dealbreaker import apply_dealbreakers
from .base import Algorithm, AlgorithmResult, OptionInput, VoteInput


class IterativeVeto(Algorithm):
    name = "iterative_veto"

    def run(
        self,
        options: List[OptionInput],
        votes: List[VoteInput],
        num_players: int,
        seed: Optional[int] = None,
    ) -> AlgorithmResult:
        live_ids: List[int] = [o.id for o in options if not o.eliminated]
        if not live_ids:
            return AlgorithmResult(winner_id=None)
        if len(live_ids) == 1:
            return AlgorithmResult(winner_id=live_ids[0], survivors=live_ids)

        majority = (num_players // 2) + 1
        eliminated_order: List[int] = []
        rounds: List[dict] = []
        trace: List[str] = []

        # Group votes by round for iterative replay. If no rounds were
        # recorded, treat everything as round 0. We keep iterating after the
        # recorded rounds run out so the algorithm always converges to a
        # single survivor — trailing rounds apply cumulative scores only.
        by_round: DefaultDict[int, List[VoteInput]] = defaultdict(list)
        for v in votes:
            by_round[v.round_number].append(v)
        recorded = sorted(by_round.keys())
        max_extra = len(live_ids)  # worst case one elimination per round
        ordered_rounds = recorded + [
            (recorded[-1] if recorded else 0) + i + 1 for i in range(max_extra)
        ]

        live_set: Set[int] = set(live_ids)
        cumulative_eliminate: Counter = Counter()
        cumulative_keep: Counter = Counter()
        dealbreaker_seen: Set[Tuple[int, int]] = set()

        for rnum in ordered_rounds:
            if len(live_set) <= 1:
                break
            bucket = by_round[rnum]

            round_dealbreaker_pairs: List[Tuple[int, int]] = []
            for v in bucket:
                if v.option_id not in live_set:
                    continue
                if v.is_dealbreaker:
                    key = (v.option_id, v.user_id)
                    if key in dealbreaker_seen:
                        continue
                    dealbreaker_seen.add(key)
                    round_dealbreaker_pairs.append(key)
                elif v.kind == "eliminate":
                    cumulative_eliminate[v.option_id] += 1
                elif v.kind == "keep":
                    cumulative_keep[v.option_id] += 1

            if round_dealbreaker_pairs:
                survivors = apply_dealbreakers(list(live_set), round_dealbreaker_pairs)
                killed = live_set - set(survivors)
                for oid in killed:
                    eliminated_order.append(oid)
                live_set = set(survivors)
                trace.append(f"round {rnum}: dealbreaker killed {sorted(killed)}")
                if len(live_set) <= 1:
                    rounds.append({"round": rnum, "survivors": sorted(live_set)})
                    break

            over_majority = {
                oid: cumulative_eliminate[oid]
                for oid in live_set
                if cumulative_eliminate[oid] >= majority
            }
            if over_majority:
                top = max(over_majority.values())
                killed = {oid for oid, c in over_majority.items() if c == top}
                if len(killed) >= len(live_set):
                    killed = {min(killed)}
                for oid in killed:
                    eliminated_order.append(oid)
                live_set -= killed
                trace.append(f"round {rnum}: majority-eliminated {sorted(killed)}")
            else:
                keep_scores: Dict[int, int] = {oid: cumulative_keep[oid] for oid in live_set}
                lowest = min(keep_scores.values())
                victim = min(oid for oid, s in keep_scores.items() if s == lowest)
                eliminated_order.append(victim)
                live_set.discard(victim)
                trace.append(f"round {rnum}: low-keep-eliminated {victim}")

            rounds.append({"round": rnum, "survivors": sorted(live_set)})

        winner = next(iter(live_set)) if len(live_set) == 1 else (sorted(live_set)[0] if live_set else None)
        return AlgorithmResult(
            winner_id=winner,
            eliminated_ids=eliminated_order,
            survivors=sorted(live_set),
            rounds=rounds,
            trace=trace,
        )
