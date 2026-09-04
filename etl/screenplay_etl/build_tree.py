"""Assigns the scene -> sequence -> act -> film tree structure and node IDs for one film.

Node ID scheme: each film gets its own block of 1000 IDs (script_id * 1000), comfortably
above any real film's node count (typically ~1 + 3 + ~10 + ~50 = ~64 nodes):
    film root:  script_id*1000 + 0
    acts:       script_id*1000 + 1, 2, 3       (fixed 3-act structure)
    sequences:  script_id*1000 + 10, 11, ...
    scenes:     script_id*1000 + 100, 101, ...

Act boundaries follow the standard 3-act proportions (Syd Field): Act I = first 25% of the
script, Act II = 25-75%, Act III = 75-100%, using each scene's `pct_position`. Sequences are
fixed-size chunks of consecutive scenes within an act (~5 scenes each) — a simplification of
the film-theory "sequence" (a connected mini-arc), not a semantic detection of one; acceptable
given the time-boxed scope (see PROGRESS.md Slice 2 log).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .films import FilmSpec
from .parse_script import RawScene

_ACT_BOUNDARIES = (0.25, 0.75)  # Act I ends at 25%, Act II ends at 75%, Act III to 100%
_SCENES_PER_SEQUENCE = 5


@dataclass
class TreeNode:
    node_id: int
    parent_id: int
    level: int  # 0=scene 1=sequence 2=act 3=film
    seq_idx: int
    pct_position: float
    slug: str = ""
    text: str = ""  # scoring/embedding input; not stored in ClickHouse directly
    children: list[int] = field(default_factory=list)


@dataclass
class Tree:
    film: FilmSpec
    nodes: dict[int, TreeNode]  # node_id -> TreeNode, all levels
    scene_ids_in_order: list[int]


def _act_index(pct_position: float) -> int:
    if pct_position < _ACT_BOUNDARIES[0]:
        return 0
    if pct_position < _ACT_BOUNDARIES[1]:
        return 1
    return 2


def build_tree(film: FilmSpec, raw_scenes: list[RawScene]) -> Tree:
    base = film.script_id * 1000
    nodes: dict[int, TreeNode] = {}

    film_id = base + 0
    act_ids = [base + 1, base + 2, base + 3]
    nodes[film_id] = TreeNode(film_id, film_id, level=3, seq_idx=0, pct_position=0.5)
    for i, act_id in enumerate(act_ids):
        nodes[act_id] = TreeNode(act_id, film_id, level=2, seq_idx=i, pct_position=0.0)
        nodes[film_id].children.append(act_id)

    # Bucket scenes into acts by pct_position, preserving script order within each act.
    scenes_by_act: list[list[RawScene]] = [[], [], []]
    for scene in raw_scenes:
        scenes_by_act[_act_index(scene.pct_position)].append(scene)

    scene_ids_in_order: list[int] = []
    next_sequence_id = base + 10
    next_scene_id = base + 100

    for act_idx, act_scenes in enumerate(scenes_by_act):
        act_id = act_ids[act_idx]
        act_positions: list[float] = []
        seq_idx_in_act = 0
        for chunk_start in range(0, len(act_scenes), _SCENES_PER_SEQUENCE):
            chunk = act_scenes[chunk_start : chunk_start + _SCENES_PER_SEQUENCE]
            if not chunk:
                continue
            sequence_id = next_sequence_id
            next_sequence_id += 1
            seq_positions = [s.pct_position for s in chunk]
            nodes[sequence_id] = TreeNode(
                sequence_id, act_id, level=1, seq_idx=seq_idx_in_act,
                pct_position=sum(seq_positions) / len(seq_positions),
            )
            nodes[act_id].children.append(sequence_id)
            seq_idx_in_act += 1
            act_positions.extend(seq_positions)

            for scene_idx_in_seq, scene in enumerate(chunk):
                scene_id = next_scene_id
                next_scene_id += 1
                nodes[scene_id] = TreeNode(
                    scene_id, sequence_id, level=0, seq_idx=scene_idx_in_seq,
                    pct_position=scene.pct_position, slug=scene.slug, text=scene.text,
                )
                nodes[sequence_id].children.append(scene_id)
                scene_ids_in_order.append(scene_id)

        if act_positions:
            nodes[act_id].pct_position = sum(act_positions) / len(act_positions)

    return Tree(film=film, nodes=nodes, scene_ids_in_order=scene_ids_in_order)
