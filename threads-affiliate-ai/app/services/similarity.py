"""Text similarity for copy-originality checks (spec section 9).

Uses a dependency-free token Jaccard + difflib ratio blend. Good enough to
catch near-duplicate / copied phrasing against researched posts and prior
candidates. If any candidate exceeds COPY_SIMILARITY_THRESHOLD it is regenerated.
"""
from __future__ import annotations

import difflib
import re
from typing import Iterable

_TOKEN_RE = re.compile(r"[0-9A-Za-z぀-ヿ一-鿿]+")


def _tokens(text: str) -> set[str]:
    # character bi-grams work better than whitespace tokens for Japanese
    cleaned = "".join(_TOKEN_RE.findall(text or ""))
    if len(cleaned) < 2:
        return set(cleaned)
    return {cleaned[i : i + 2] for i in range(len(cleaned) - 1)}


def similarity(a: str, b: str) -> float:
    """Return a 0..1 similarity score between two texts."""
    if not a or not b:
        return 0.0
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        jaccard = 0.0
    else:
        jaccard = len(ta & tb) / len(ta | tb)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return round(max(jaccard, ratio), 4)


def max_similarity(text: str, corpus: Iterable[str]) -> float:
    """Highest similarity of `text` against any string in `corpus`."""
    best = 0.0
    for other in corpus:
        best = max(best, similarity(text, other))
        if best >= 0.999:
            break
    return best
