-- Slice 1 walking-skeleton seed: ONE tiny produced-film tree (10 rows) so the agent
-- has something real to query end-to-end. Throwaway data; Slice 2 replaces it with the
-- ETL-loaded corpus. Embeddings here are 4-float placeholders (real ones are set in Slice 2).
--
-- Tree for script_id=1 "THE LAST SIGNAL" (thriller):
--   1 film root -> 3 acts -> 6 scenes = 10 nodes.

INSERT INTO script_nodes
(script_id, node_id, parent_id, level, seq_idx, pct_position, is_corpus, genre, year, title,
 valence, conflict, arousal, char_ids, line_count, summary, slug, embedding) VALUES
-- film root (level 3)
(1, 1, 1, 3, 0, 0.50, 1, 'thriller', 2019, 'THE LAST SIGNAL', -0.12, 0.61, 0.55, [1,2,3], 480,
 'A codebreaker races a shrinking clock as trust collapses around her.', '', [0.1,0.2,0.3,0.4]),
-- acts (level 2)
(1, 2, 1, 2, 0, 0.17, 1, 'thriller', 2019, 'THE LAST SIGNAL',  0.20, 0.35, 0.40, [1,2],   150,
 'Setup: the signal is discovered and the team assembles.', '', [0.1,0.2,0.3,0.4]),
(1, 3, 1, 2, 1, 0.50, 1, 'thriller', 2019, 'THE LAST SIGNAL', -0.25, 0.70, 0.60, [1,2,3], 190,
 'Confrontation: alliances fracture as the deadline nears.', '', [0.1,0.2,0.3,0.4]),
(1, 4, 1, 2, 2, 0.83, 1, 'thriller', 2019, 'THE LAST SIGNAL', -0.30, 0.78, 0.66, [1,3],   140,
 'Resolution: the final decryption at maximum cost.', '', [0.1,0.2,0.3,0.4]),
-- scenes (level 0) under act 2
(1, 5, 2, 0, 0, 0.08, 1, 'thriller', 2019, 'THE LAST SIGNAL',  0.35, 0.20, 0.30, [1],     70,
 'The codebreaker intercepts an impossible transmission.', 'INT. LAB - NIGHT', [0.1,0.2,0.3,0.4]),
(1, 6, 2, 0, 1, 0.25, 1, 'thriller', 2019, 'THE LAST SIGNAL',  0.05, 0.50, 0.50, [1,2],   80,
 'Her handler pulls her into a black operation.', 'INT. SAFEHOUSE - DAY', [0.1,0.2,0.3,0.4]),
-- scenes under act 3
(1, 7, 3, 0, 0, 0.45, 1, 'thriller', 2019, 'THE LAST SIGNAL', -0.20, 0.65, 0.58, [1,2,3], 95,
 'A trusted ally is exposed as the leak.', 'INT. OPS ROOM - NIGHT', [0.1,0.2,0.3,0.4]),
(1, 8, 3, 0, 1, 0.55, 1, 'thriller', 2019, 'THE LAST SIGNAL', -0.30, 0.75, 0.62, [1,3],   95,
 'The team splinters under the accusation.', 'EXT. ROOFTOP - NIGHT', [0.1,0.2,0.3,0.4]),
-- scenes under act 4
(1, 9, 4, 0, 0, 0.80, 1, 'thriller', 2019, 'THE LAST SIGNAL', -0.28, 0.80, 0.70, [1,3],   72,
 'A desperate hand-off goes wrong.', 'EXT. DOCKS - NIGHT', [0.1,0.2,0.3,0.4]),
(1, 10, 4, 0, 1, 0.88, 1, 'thriller', 2019, 'THE LAST SIGNAL', -0.32, 0.76, 0.62, [1],    68,
 'She decrypts the last signal alone.', 'INT. LAB - DAWN', [0.1,0.2,0.3,0.4]);
