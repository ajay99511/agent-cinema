"""Deterministic scene scoring from the NRC VAD lexicon. No LLM — see the plan's decision
record: cost, rate limits, and determinism (parent numbers must not drift between runs).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .lexicon import load_lexicon

_WORD_RE = re.compile(r"[a-zA-Z']+")


@dataclass(frozen=True)
class SceneScore:
    valence: float
    arousal: float
    dominance: float
    conflict: float
    scored_word_count: int


def score_text(text: str) -> SceneScore:
    """Average VAD over lexicon-matched words in `text`; conflict is derived from V+A.

    Conflict is our own explicit, deterministic formula (the plan calls it "NRC-derived"
    without pinning exact math): high arousal + negative valence = tension. Both components
    are rescaled from [-1, 1] to [0, 1] and multiplied, so a scene must be BOTH aroused AND
    negative to score high — calm scenes and purely-positive-but-energetic scenes both stay
    low, matching the intuitive meaning of narrative "conflict."
    """
    lexicon = load_lexicon()
    words = _WORD_RE.findall(text.lower())

    matched = [lexicon[w] for w in words if w in lexicon]
    if not matched:
        # Edge case (plan §"Edge cases"): a scene with no NRC-scorable words (e.g. all-caps
        # slugline-only stub, or a scene of pure non-English/onomatopoeia text). Neutral,
        # not fabricated — the aggregate over its siblings still means something.
        return SceneScore(valence=0.0, arousal=0.0, dominance=0.0, conflict=0.0, scored_word_count=0)

    n = len(matched)
    valence = sum(v for v, _, _ in matched) / n
    arousal = sum(a for _, a, _ in matched) / n
    dominance = sum(d for _, _, d in matched) / n

    valence_component = (1.0 - valence) / 2.0  # negative valence -> higher
    arousal_component = (arousal + 1.0) / 2.0  # positive arousal -> higher
    conflict = valence_component * arousal_component

    return SceneScore(
        valence=valence,
        arousal=arousal,
        dominance=dominance,
        conflict=conflict,
        scored_word_count=n,
    )
