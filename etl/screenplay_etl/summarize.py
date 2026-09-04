"""Gemini prose summaries — PROSE ONLY, never a source of numeric fields (guardrail #4).

Scene summaries are batched (one call per ~8 scenes, structured JSON output) to keep total
call count manageable across a ~25-film corpus. Parent summaries are one call each, built
from their already-generated child summaries rather than re-reading raw scene text — cheap,
and keeps the summary chain traceable (a film's summary is literally built from its acts',
which are built from their sequences', which are built from their scenes').
"""

from __future__ import annotations

import json
import time

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"
_SCENE_BATCH_SIZE = 8
_MAX_SCENE_CHARS = 1500  # keep prompts small; a scene's opening + middle is enough context
_MAX_RETRIES = 4
_THROTTLE_SECONDS = 2.0


def _generate_json_list(client: genai.Client, prompt: str, expected_len: int) -> list[str] | None:
    for attempt in range(_MAX_RETRIES):
        try:
            result = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[str],
                    temperature=0.2,
                ),
            )
            time.sleep(_THROTTLE_SECONDS)
            parsed = json.loads(result.text)
            if isinstance(parsed, list) and len(parsed) == expected_len:
                return [str(s).strip() for s in parsed]
            return None
        except Exception as e:
            is_quota = "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)
            if attempt == _MAX_RETRIES - 1:
                return None
            time.sleep(30.0 if is_quota else 2**attempt)
    return None


def summarize_scenes(client: genai.Client, scene_texts: list[str]) -> list[str]:
    """One-sentence, plain-fact summary per scene, in input order."""
    out: list[str] = []
    for start in range(0, len(scene_texts), _SCENE_BATCH_SIZE):
        batch = scene_texts[start : start + _SCENE_BATCH_SIZE]
        numbered = "\n\n".join(
            f"SCENE {i + 1}:\n{text[:_MAX_SCENE_CHARS]}" for i, text in enumerate(batch)
        )
        prompt = (
            "For each numbered screenplay scene below, write ONE short plain-English sentence "
            "stating what happens (no scores, no opinions, just the key action/event). "
            f"Return a JSON array of exactly {len(batch)} strings, one per scene, in order.\n\n"
            f"{numbered}"
        )
        result = _generate_json_list(client, prompt, len(batch))
        if result is not None:
            out.extend(result)
            continue
        # Fallback: one call per scene in this batch (only hit on a malformed batch response).
        for text in batch:
            single = _generate_json_list(
                client,
                "Write ONE short plain-English sentence stating what happens in this "
                f"screenplay scene (no scores, no opinions):\n\n{text[:_MAX_SCENE_CHARS]}",
                1,
            )
            out.append(single[0] if single else "")
    return out


def summarize_parent(client: genai.Client, title: str, level_name: str, child_summaries: list[str]) -> str:
    """One short sentence describing this act/sequence/film's arc, from its children's summaries."""
    joined = " ".join(s for s in child_summaries if s)
    prompt = (
        f'Given these plain-English event summaries, in order, from the {level_name} of the '
        f'screenplay "{title}", write ONE short sentence describing the overall arc of this '
        f"{level_name} (no scores, no opinions):\n\n{joined[:_MAX_SCENE_CHARS * 3]}"
    )
    result = _generate_json_list(client, prompt + "\n\nReturn a JSON array containing exactly 1 string.", 1)
    return result[0] if result else ""
