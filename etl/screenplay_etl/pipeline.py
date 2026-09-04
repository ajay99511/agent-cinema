"""Processes one film end-to-end: fetch -> parse -> tree -> score -> embed -> summarize ->
aggregate parents -> rows ready for db.insert_rows.

Parent numeric fields (valence/conflict/arousal/line_count/embedding) are computed here in
Python as a plain mean/sum/centroid over each node's direct children — arithmetically
identical to what `AVG()`/`SUM()` would compute over the same rows in SQL. The guardrail this
protects ("numbers are aggregates, never LLM-guessed") is verified for real after loading:
Slice 2's acceptance check re-derives each parent's valence via a live
`SELECT avg(valence) ... GROUP BY parent_id` query and compares it to the stored value — see
run.py's `verify_film`. Computing it here rather than via an extra ClickHouse round-trip per
film is simpler and faster; the post-load SQL check is what actually proves the invariant,
not where the arithmetic happens.
"""

from __future__ import annotations

from google import genai

from .build_tree import Tree, TreeNode, build_tree
from .embed import embed_texts, mean_embedding
from .films import FilmSpec
from .parse_script import parse_script
from .score import score_text
from .summarize import summarize_parent, summarize_scenes

_EMBED_TEXT_CAP = 4000  # characters; keeps embedding calls well under any input-length limit


def _line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def process_film(film: FilmSpec, client: genai.Client) -> list[dict]:
    raw_scenes = parse_script(film.url)
    if not raw_scenes:
        raise ValueError(f"{film.title}: no scenes parsed from {film.url}")

    tree = build_tree(film, raw_scenes)

    # --- Scene-level: score (deterministic, no LLM), embed + summarize (Vertex/Gemini) ---
    scene_nodes = [tree.nodes[nid] for nid in tree.scene_ids_in_order]
    scene_texts = [n.text for n in scene_nodes]

    scores = [score_text(t) for t in scene_texts]
    embeddings = embed_texts(client, [t[:_EMBED_TEXT_CAP] for t in scene_texts])
    summaries = summarize_scenes(client, scene_texts)

    scene_data: dict[int, dict] = {}
    for node, sc, emb, summ in zip(scene_nodes, scores, embeddings, summaries):
        scene_data[node.node_id] = {
            "valence": sc.valence, "conflict": sc.conflict, "arousal": sc.arousal,
            "embedding": emb, "summary": summ, "line_count": _line_count(node.text),
        }

    # --- Bottom-up parent aggregation: sequences (level 1) -> acts (2) -> film (3) ---
    node_data: dict[int, dict] = dict(scene_data)
    for level in (1, 2, 3):
        for node in [n for n in tree.nodes.values() if n.level == level]:
            children = sorted(
                (tree.nodes[cid] for cid in node.children), key=lambda c: c.seq_idx
            )
            child_rows = [node_data[c.node_id] for c in children]
            n = len(child_rows)
            level_name = {1: "sequence", 2: "act", 3: "film"}[level]
            summary = summarize_parent(
                client, film.title, level_name, [r["summary"] for r in child_rows]
            )
            node_data[node.node_id] = {
                "valence": sum(r["valence"] for r in child_rows) / n,
                "conflict": sum(r["conflict"] for r in child_rows) / n,
                "arousal": sum(r["arousal"] for r in child_rows) / n,
                "embedding": mean_embedding([r["embedding"] for r in child_rows]),
                "summary": summary,
                "line_count": sum(r["line_count"] for r in child_rows),
            }

    return _to_rows(tree, node_data)


def _to_rows(tree: Tree, node_data: dict[int, dict]) -> list[dict]:
    film = tree.film
    rows = []
    for node_id, node in tree.nodes.items():
        data = node_data[node_id]
        rows.append({
            "script_id": film.script_id,
            "node_id": node.node_id,
            "parent_id": node.parent_id,
            "level": node.level,
            "seq_idx": node.seq_idx,
            "pct_position": node.pct_position,
            "is_corpus": 1,
            "genre": film.genre,
            "year": film.year,
            "title": film.title,
            "valence": data["valence"],
            "conflict": data["conflict"],
            "arousal": data["arousal"],
            "char_ids": [],  # not populated — see films.py module docstring
            "line_count": data["line_count"],
            "summary": data["summary"],
            "slug": node.slug,  # empty for every level above scenes, by design
            "embedding": data["embedding"],
        })
    return rows
