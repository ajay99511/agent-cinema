"""Vertex AI embeddings — the only permitted AI provider (hackathon hard rule).

Model + dim locked empirically (Session 5 spike): `gemini-embedding-001` at 768 dims works
via Vertex AI through the same ADC/service-account auth path already proven in Slice 1.
768 was chosen over the max 3072 as the documented quality/storage tradeoff point for a
~1,000-scene corpus where exact `cosineDistance` scan cost matters more than marginal recall.
"""

from __future__ import annotations

import time

from google import genai
from google.genai import types

MODEL = "gemini-embedding-001"
DIMENSIONS = 768
_BATCH_SIZE = 20
_MAX_RETRIES = 6
# This project's Vertex trial quota for embed_content is low (hit 429 RESOURCE_EXHAUSTED at
# default settings — see PROGRESS.md Slice 2 log). One request per batch stays well under it.
_THROTTLE_SECONDS = 3.0


def embed_texts(client: genai.Client, texts: list[str]) -> list[list[float]]:
    """Batched RETRIEVAL_DOCUMENT embeddings, in input order."""
    out: list[list[float]] = []
    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        for attempt in range(_MAX_RETRIES):
            try:
                result = client.models.embed_content(
                    model=MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=DIMENSIONS,
                    ),
                )
                out.extend(list(e.values) for e in result.embeddings)
                break
            except Exception as e:
                is_quota = "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)
                if attempt == _MAX_RETRIES - 1:
                    raise
                time.sleep(30.0 if is_quota else 2**attempt)
        time.sleep(_THROTTLE_SECONDS)
    return out


def mean_embedding(vectors: list[list[float]]) -> list[float]:
    """Parent-node embedding = centroid of its children's embeddings.

    A cheap, deterministic, well-established way to give non-leaf nodes a representative
    vector without extra API calls — no LLM/embedding-model call for parent nodes at all,
    consistent with "parents are aggregates, not model output."
    """
    if not vectors:
        return [0.0] * DIMENSIONS
    n = len(vectors)
    return [sum(v[i] for v in vectors) / n for i in range(len(vectors[0]))]
