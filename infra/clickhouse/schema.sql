-- script_nodes: the single table holding BOTH the produced-film corpus (is_corpus=1)
-- and any user-uploaded draft (is_corpus=0), at every level of the screenplay tree.
--
-- This schema is a ONE-WAY DOOR (see docs/plans/agentic-cinema-screenplay-map.md §4):
-- changing it after the corpus is loaded forces a full ETL re-run. Change deliberately.
--
-- Sort-key rationale:
--   is_corpus first  -> "my draft vs. everything else" is a partition-pruned scan
--   level next       -> "all Act nodes" (RAPTOR tree-traversal = WHERE level=2) is a range read
--   genre next       -> cohort filtering happens BEFORE any vector math (filter-first search)

CREATE TABLE IF NOT EXISTS script_nodes
(
    script_id     UInt32,                 -- one per film or per uploaded draft
    node_id       UInt32,                 -- unique within a script
    parent_id     UInt32,                 -- self/sentinel for a film-level root
    level         UInt8,                  -- 0=scene (leaf) 1=sequence 2=act 3=film
    seq_idx       UInt16,                 -- position among siblings
    pct_position  Float32,                -- 0..1 through the script (basis for position cohorts)
    is_corpus     UInt8,                  -- 1=produced film, 0=user draft
    genre         LowCardinality(String),
    year          UInt16,
    title         String,                 -- film title, or "MY DRAFT"
    valence       Float32,                -- NRC VAD; scene: computed, parent: AVG(children)
    conflict      Float32,                -- NRC-derived; parent: AVG(children)
    arousal       Float32,                -- NRC VAD; scene: computed, parent: AVG(children)
    char_ids      Array(UInt32),          -- characters present
    line_count    UInt16,                 -- parent: SUM(children)
    summary       String,                 -- model-generated PROSE ONLY (never numbers)
    slug          String,                 -- scene heading; leaf only
    embedding     Array(Float32)          -- Vertex text-embedding; fixed dim across corpus + drafts
)
ENGINE = MergeTree
ORDER BY (is_corpus, level, genre, script_id, seq_idx);
