"""Offline unit tests for the pure logic in tools.py. The ClickHouse-dependent parts
(scene_percentiles, similar_scenes) are verified against the live corpus instead — see
PROGRESS.md Slice 3 log for that evidence (real cohort counts, real percentiles, real
embedding-distance results including a correctly-excluded self-match).
"""

from __future__ import annotations

from screenplay_agent.tools import _position_bucket, MIN_COHORT_N


def test_position_bucket_boundaries():
    assert _position_bucket(0.0) == (0.0, 0.25)
    assert _position_bucket(0.24) == (0.0, 0.25)
    assert _position_bucket(0.25) == (0.25, 0.75)  # boundary is inclusive on the low end
    assert _position_bucket(0.74) == (0.25, 0.75)
    assert _position_bucket(0.75) == (0.75, 1.0)
    assert _position_bucket(1.0) == (0.75, 1.0)


def test_min_cohort_n_matches_plan_default():
    assert MIN_COHORT_N == 20
