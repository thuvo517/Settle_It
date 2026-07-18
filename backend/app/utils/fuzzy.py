"""Fuzzy duplicate detection for option submissions.

We normalize text (lowercase, strip punctuation, collapse whitespace) and
compare against existing options using token-set ratio. Two options above the
threshold are treated as duplicates; the later submission is rejected so the
earlier author is credited.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Optional

from rapidfuzz import fuzz

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def similarity(a: str, b: str) -> int:
    if not a or not b:
        return 0
    return int(fuzz.token_set_ratio(a, b))


def find_duplicate(candidate: str, existing: Iterable[str], threshold: int = 85) -> Optional[str]:
    """Return the first existing entry that is a fuzzy duplicate of candidate.

    Both ``candidate`` and ``existing`` entries should already be normalized.
    """
    if not candidate:
        return None
    best: Optional[str] = None
    best_score = -1
    for ex in existing:
        if not ex:
            continue
        score = similarity(candidate, ex)
        if score >= threshold and score > best_score:
            best = ex
            best_score = score
    return best
