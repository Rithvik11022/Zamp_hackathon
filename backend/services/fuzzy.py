from __future__ import annotations

from difflib import SequenceMatcher


def token_sort_ratio(s1: str, s2: str) -> float:
    """Pure-Python replacement for rapidfuzz.fuzz.token_sort_ratio.

    Returns a similarity score between 0 and 100.
    """
    tokens1 = " ".join(sorted(s1.lower().split()))
    tokens2 = " ".join(sorted(s2.lower().split()))
    return SequenceMatcher(None, tokens1, tokens2).ratio() * 100
