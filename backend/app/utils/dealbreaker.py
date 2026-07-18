"""Dealbreaker logic.

A dealbreaker is a "hard veto" cast during the voting phase. Any option that
accumulates at least one dealbreaker vote is eliminated immediately regardless
of the other voting tallies, provided there is still at least one option
remaining after the dealbreaker sweep.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Tuple


def apply_dealbreakers(
    option_ids: Iterable[int],
    dealbreaker_votes: Iterable[Tuple[int, int]],  # (option_id, user_id)
) -> List[int]:
    """Return surviving option ids after dealbreaker sweep.

    If applying dealbreakers would eliminate ALL options, we preserve the
    option(s) with the fewest dealbreakers so there is always a winner.
    """
    option_ids = list(option_ids)
    if not option_ids:
        return []

    counts: Counter[int] = Counter()
    seen: set[Tuple[int, int]] = set()
    for opt_id, user_id in dealbreaker_votes:
        key = (opt_id, user_id)
        if key in seen:
            continue
        seen.add(key)
        counts[opt_id] += 1

    vetoed = {oid for oid in option_ids if counts.get(oid, 0) > 0}
    survivors = [oid for oid in option_ids if oid not in vetoed]
    if survivors:
        return survivors

    min_count = min(counts[oid] for oid in option_ids)
    return [oid for oid in option_ids if counts[oid] == min_count]
