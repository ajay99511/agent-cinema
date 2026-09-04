"""IMSDb screenplay fetch + scene segmentation.

IMSDb page formatting varies a lot between scripts (some are clean OCR'd shooting scripts,
some are loose as-broadcast transcripts with no standard sluglines at all). Rather than
build a heuristic general enough for arbitrary formats, `films.py`'s curated list was
pre-screened: only titles whose page has a healthy count of real INT./EXT. sluglines were
kept (verified empirically before adding any title — see PROGRESS.md Slice 2 log).
"""

from __future__ import annotations

import html as ihtml
import re
from dataclasses import dataclass

import httpx

_PRE_RE = re.compile(r"<pre>(.*?)</pre>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_HEADING_RE = re.compile(r"^[ \t]*((?:INT|EXT|I/E)[./\s-][^\n]*)", re.I | re.M)


@dataclass(frozen=True)
class RawScene:
    slug: str
    text: str
    pct_position: float  # midpoint of the scene's character span / total script length


def fetch_script_text(url: str) -> str:
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    match = _PRE_RE.search(resp.text)
    if not match:
        raise ValueError(f"no <pre> block found at {url}")
    text = _TAG_RE.sub("", match.group(1))
    return ihtml.unescape(text)


def split_scenes(full_text: str) -> list[RawScene]:
    headings = list(_HEADING_RE.finditer(full_text))
    if not headings:
        return []
    doc_len = len(full_text)
    scenes: list[RawScene] = []
    for i, m in enumerate(headings):
        start = m.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else doc_len
        slug = " ".join(m.group(1).split())[:120].upper()
        midpoint = (start + end) / 2.0
        scenes.append(RawScene(slug=slug, text=full_text[start:end], pct_position=midpoint / doc_len))
    return scenes


def parse_script(url: str) -> list[RawScene]:
    return split_scenes(fetch_script_text(url))
