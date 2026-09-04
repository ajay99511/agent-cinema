"""NRC VAD Lexicon loader.

Source: https://saifmohammad.com/WebPages/nrc-vad.html (v2.1, March 2025).
Free for non-commercial research/educational use (this hackathon qualifies) — NOT for
redistribution. Downloaded once into etl/data/ (gitignored); never commit the lexicon file
itself. If etl/data/ is missing, re-download with:
    curl -L -o etl/data/nrc-vad.zip https://saifmohammad.com/WebDocs/Lexicons/NRC-VAD-Lexicon-v2.1.zip
    unzip etl/data/nrc-vad.zip -d etl/data/nrc-vad
"""

from __future__ import annotations

import functools
from pathlib import Path

_LEXICON_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "nrc-vad"
    / "NRC-VAD-Lexicon-v2.1"
    / "Unigrams"
    / "unigrams-NRC-VAD-Lexicon-v2.1.txt"
)


@functools.lru_cache(maxsize=1)
def load_lexicon() -> dict[str, tuple[float, float, float]]:
    """word -> (valence, arousal, dominance), each in [-1, 1]."""
    if not _LEXICON_PATH.exists():
        raise FileNotFoundError(
            f"NRC VAD lexicon not found at {_LEXICON_PATH}. See module docstring to re-download."
        )
    lexicon: dict[str, tuple[float, float, float]] = {}
    with _LEXICON_PATH.open(encoding="utf-8") as f:
        next(f)  # header: term\tvalence\tarousal\tdominance
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4:
                continue
            term, v, a, d = parts
            lexicon[term.lower()] = (float(v), float(a), float(d))
    return lexicon
