from .base import AlgorithmResult, OptionInput, VoteInput
from .weighted_random import WeightedRandom
from .bracket import Bracket
from .iterative_veto import IterativeVeto

ALGORITHMS = {
    "weighted_random": WeightedRandom,
    "bracket": Bracket,
    "iterative_veto": IterativeVeto,
}


def get_algorithm(name: str):
    if name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {name}")
    return ALGORITHMS[name]()


__all__ = [
    "ALGORITHMS",
    "get_algorithm",
    "AlgorithmResult",
    "OptionInput",
    "VoteInput",
    "WeightedRandom",
    "Bracket",
    "IterativeVeto",
]
