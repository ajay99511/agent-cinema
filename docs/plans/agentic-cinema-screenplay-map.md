# Plan: Screenplay Structural Map — ClickHouse-native agent for the screenwriter-in-revision

**Tier:** Foundational (greenfield; the data model is a one-way door and the whole product rests on it)
**Author / date:** Planning session, 2026-08-17
**Status:** Draft — ready for implementation once Open Questions Q1/Q2 are closed
**Event:** Agentic Cinema hackathon — ClickHouse track. **Submit by Sept 7, 2026, 2:00pm PT** (treat the site's Sept 9 date as unreliable buffer, not the target).

---

## 0. Context an implementor needs before reading

This is a hackathon submission, not a durable product. Optimize for a **complete, coherent, demo-able product that scores against a fixed rubric**, then stop. The four equally-weighted judging criteria *are* the acceptance bar:

1. **Technological Implementation** — how well it's built + how effectively it uses Google Cloud **and ClickHouse at runtime**.
2. **Design** — a complete product experience, not a proof of concept.
3. **Potential Impact** — a credible, specific real problem for a real audience, actually solved as shown.
4. **Quality of the Idea** — creative, non-obvious use; genuine grasp of the problem space.

**Two hard track rules that are disqualifiers if missed:**
- All AI must be **Google Cloud** (Gemini via Vertex AI). **No** AWS/Azure/OpenAI/Anthropic in the AI path. Non-AI third-party services are allowed.
- **ClickHouse must be queried at runtime via its official MCP server**, connected to a ClickHouse Cloud (or self-hosted) cluster. ClickHouse being a passive file store = Stage-1 fail.

**The non-negotiable design principle (repeated because it is the whole game):** every number the user sees comes from a SQL query against ClickHouse at request time. The frontend never computes analytics from a cached JSON blob. Brushing the arc fires a query; zooming changes which tree `level` is read. If a pixel can't be traced to a `SELECT`, it's a bug.

---

## 1. Problem and outcome

**Outcome:** A screenwriter mid-rewrite can *see the shape of their own draft* — its emotional and structural arc — in minutes instead of days, with every observation localized to a specific scene and expressed as a **defensible comparison against produced films** ("this scene is in the bottom 8% for conflict density among scenes at this act-position in produced thrillers"), never as an opaque score ("6/10").

**Users / actors:**
- **Primary user:** the screenwriter revising a draft. Journey today: re-read 120 pages to answer "does my antagonist vanish in Act II?"; costs an afternoon and yields a subjective guess.
- **Secondary user / market:** the development executive / coverage desk who reads dozens of scripts and needs fast, comparable structural reads. Same tool, framed as the buyer in the pitch.

**Domain context:** A **screenplay is a pre-built hierarchy** — line → scene (slugline-delimited) → sequence → act → film. This is the key insight: we get a RAPTOR-style retrieval tree *for free from formatting*, interpretable (a writer knows what "Act II" is; nobody knows what "GMM cluster 7" is) and with no fragile clustering step. Nodes at every level live in one ClickHouse table alongside a produced-film corpus.

**Invariants:**
- Every node has exactly one `parent_id` except film-level roots (`parent_id = node_id` or a sentinel); the tree is acyclic.
- `level` is ordered: 0 = scene (leaf), 1 = sequence, 2 = act, 3 = film. Higher = more abstract.
- **Numeric fields on a parent are deterministic SQL aggregates over its children** (`AVG`, `SUM`, percentile) — never LLM-generated. Only the `summary` prose is model-generated. (This is the error-propagation mitigation: noise cannot compound up the tree through the numbers.)
- `is_corpus = 1` for produced-film reference data, `0` for a user's uploaded draft. The corpus is immutable during a session; draft rows are per-session and disposable.
- Percentile claims are only emitted when the comparison cohort has **N ≥ a stated minimum** (see Q3); below that, the UI says "insufficient corpus" rather than inventing a percentile.

**Acceptance criteria:**
- [ ] A user opens the app, sees an interactive emotional/structural arc of a **pre-loaded demo draft**, and can click any point to drill from film → act → sequence → scene.
- [ ] Brushing/selecting a region of the arc issues a **new ClickHouse query** scoped to those scenes (verifiable in a network/query log), not a client-side array filter.
- [ ] The user asks, in natural language, "which of my scenes are structurally unusual, and compared to what?" and gets an answer that names specific scenes and gives **percentile positions vs. the corpus**, produced by SQL run through the ClickHouse MCP tool.
- [ ] Every displayed number is reproducible by running one SQL statement shown in the UI ("show the SQL" affordance) against the cluster.
- [ ] A user can **upload their own screenplay** (at least one supported format), have it parsed/scored/embedded/inserted as `is_corpus=0`, and get the same analysis. *(May be demo-scripted if time-constrained — see slices.)*
- [ ] The whole thing is deployed to a public URL; the agent runs on Vertex AI Agent Engine; the repo is public with an OSI license and runtime instructions.
- [ ] A ≤3-minute demo video shows it working end-to-end and shows the SQL firing.

**Non-goals:**
- Not scoring writing *quality* or giving prose feedback ("this dialogue is weak"). We report structure and emotion, positionally. (Keeps us out of subjective, indefensible territory.)
- Not whole-script LLM extraction in one pass — scene-level keeps extraction in the reliable tier.
- Not a general RAG chatbot over screenplays. The tree + percentile analytics is the product; freeform Q&A is a thin layer on top, not the point.
- Not multi-user accounts, auth, persistence of user drafts beyond a session, billing, or collaboration.
- Not the HNSW/ANN index (see Design — exact search is correct at this scale).
- Not full IMSDb (~1,100 scripts). We right-size N (Q3).

**Constraints:**
- **~2–3 hrs/day, part-time, ~3 weeks.** This dominates slicing: a complete product must exist by ~day 10, leaving runway for the corpus to grow and the video to be polished.
- **Budget ~$0** — Google Cloud $300 trial + ClickHouse Cloud $300/30-day trial. Guardrail: a $50 GCP budget alert; scale the ClickHouse service down when idle.
- Team: solo/small, full-stack (Next.js/Node strong; Python for ADK is the newer surface).

**Assumptions (load-bearing marked ⚠):**
- ⚠ **A cleanly parsed screenplay dataset exists and is licensed for this use** (ScriptBase / ScreenPy / pre-parsed IMSDb). Verified in Slice 2's spike; if false, fall back to a hand-curated ~30–50 script set. → Q1.
- ⚠ **The ClickHouse MCP server exposes query execution callable as an ADK tool** and works against ClickHouse Cloud. Verified in Slice 1 (the whole skeleton is built to test exactly this). → Q2.
- Exact `cosineDistance` over ≤~500k vectors is single-digit-ms to low-hundreds-ms — acceptable for an interactive demo. (Backed by ClickHouse docs on exact vector search; re-confirmed in Slice 3.)
- NRC VAD lexicon is an acceptable, literature-standard proxy for scene valence/conflict for a hackathon.

---

## 2. Current state

**What exists today:** Nothing. Empty git repo on `master`. Greenfield — no existing patterns to honor, which means every convention below is a fresh decision, and the schema decision is therefore un-cushioned by precedent (extra reason to treat it as the one-way door it is).

**Reusable / external building blocks:**
- **ADK + Agent Engine** (`pip install "google-cloud-aiplatform[agent_engines,adk]>=1.101.0"`) — agent runtime + serverless deploy.
- **ClickHouse MCP server** — the mandated runtime tool; wrapped as an ADK tool.
- **Gemini via Vertex AI** — embeddings (`text-embedding` model) + parent-node summaries + NL→intent.
- **NRC VAD lexicon** — deterministic valence/conflict scoring (no LLM, no cost).
- **A screenplay parser** — ScreenPy or equivalent, to segment into scenes + the four elements.
- **Next.js** — frontend; a charting lib (e.g. visx/d3) for the arc.

**Must not break:** N/A (greenfield). The only "must not break" is the **submission gates** — public repo, license, deployed URL, runtime ClickHouse+Google usage.

---

## 3. Design

**Approach in one paragraph:** An **offline pipeline** ingests a parsed screenplay corpus, segments each film into a scene→sequence→act→film tree, scores each scene's valence/conflict with the NRC VAD lexicon (deterministic), embeds each node's text with Vertex AI, computes parent numeric fields as SQL aggregates, and loads everything into a single ClickHouse `script_nodes` table with `is_corpus=1`. At **runtime**, a Next.js app talks to an **ADK agent on Vertex AI Agent Engine**; the agent uses the **ClickHouse MCP server** as a tool to run parameterized SQL — exact `cosineDistance` vector search *filtered first* by genre/level/position, plus percentile aggregations comparing a scene against the corpus cohort. A user can upload a draft, which runs the same offline steps on-demand and inserts rows with `is_corpus=0`; the analysis is then "my draft's numbers vs. `AVG()`/percentile over the corpus" — the *same query shape* serves both because `is_corpus` is the leading sort key.

**Contracts** (precise enough to test):

*ClickHouse schema — the one-way door. Get this right before anything else.*
```sql
CREATE TABLE script_nodes (
  script_id      UInt32,                       -- one per film or draft
  node_id        UInt32,                       -- unique within script
  parent_id      UInt32,                       -- self/sentinel for film root
  level          UInt8,                        -- 0=scene 1=sequence 2=act 3=film
  seq_idx        UInt16,                        -- position among siblings
  pct_position   Float32,                       -- 0..1 through the script (act-position basis for cohorts)
  is_corpus      UInt8,                         -- 1=produced film, 0=user draft
  genre          LowCardinality(String),
  year           UInt16,
  title          String,                        -- film title / "MY DRAFT"
  valence        Float32,                        -- NRC VAD, scene: computed; parent: AVG of children
  conflict       Float32,                        -- NRC-derived; parent: AVG of children
  arousal        Float32,
  char_ids       Array(UInt32),                  -- characters present
  line_count     UInt16,                          -- parent: SUM of children
  summary        String,                          -- model-generated PROSE only (never numbers)
  slug           String,                          -- scene heading, leaf only
  embedding      Array(Float32)                   -- Vertex text-embedding; fixed dim (see Q4)
) ENGINE = MergeTree
ORDER BY (is_corpus, level, genre, script_id, seq_idx);
```
Sort-key rationale: leading `is_corpus` makes "my draft vs. everything else" a partition-pruned scan; `level` next makes "give me all Act nodes" (RAPTOR tree-traversal = `WHERE level=2`; collapsed = no level filter) a range read; `genre` supports cohort filtering before vector math.

*Agent tool surface (ADK tools wrapping MCP + helpers):*
- `run_scoped_sql(sql: str) -> rows` — executes read-only SQL via ClickHouse MCP. The agent's primary muscle. **Read-only**; reject non-`SELECT`.
- `scene_percentiles(script_id, node_id) -> {metric: percentile}` — canned parameterized query: this scene's valence/conflict vs. same-`pct_position`-bucket, same-`genre`, `is_corpus=1` cohort. Returns percentile + cohort N (for the N≥min invariant).
- `similar_scenes(script_id, node_id, k, filters) -> rows` — filter-first (`WHERE genre=… AND level=0 AND is_corpus=1`) then `ORDER BY cosineDistance(embedding, :vec) LIMIT k`.
- `arc(script_id, level) -> rows` — ordered nodes for the chart at a given tree level.

*Frontend ↔ agent contract:* single POST endpoint (agent's REST/HTTP interface on Agent Engine) taking `{session_id, message, context:{script_id, selection?}}` and returning `{answer, sql_shown[], data[]}`. The `sql_shown` array is what powers the "show the SQL" affordance and is the proof-of-runtime for judges.

**Data flow (main path — NL question):**
1. UI sends question + current selection → agent.
2. Agent classifies intent (compare / find-unusual / describe / similar).
3. Agent calls the matching tool → tool runs SQL via MCP against ClickHouse Cloud.
4. Agent composes a natural-language answer *from the returned rows*, attaches `sql_shown` + `data`.
5. UI renders answer + updates chart from `data`; "show SQL" reveals `sql_shown`.
- **Failure at step 3** (MCP/cluster down): tool returns a typed error; agent says "couldn't reach the data" — never fabricates numbers. This is a correctness invariant, not just UX.

**Cross-cutting:**
- **Authz:** None (single demo tenant, no accounts). Explicitly a non-goal. The one guard: the SQL tool is **read-only** and rejects mutations, so a prompt-injected "DROP TABLE" can't fire.
- **Validation:** Uploaded scripts validated for parseability before scoring; reject > size cap. SQL tool allowlists `SELECT`.
- **Observability:** Log every tool call with the emitted SQL + row count + latency. This log *is* the demo evidence and the debugging surface.
- **Performance:** Interactive queries budgeted < ~500ms P95 at N≈100–300 films. Exact vector scan is fine here; if it isn't, cohort filters shrink the scan, not an ANN index.
- **Secrets:** ClickHouse creds + any keys in **Secret Manager**, never in repo. `.env.example` only.
- **Safety:** Configure Gemini safety settings (cheap "production-ready" points).
- **i18n/a11y:** N/A for a demo, beyond not breaking keyboard nav on the chart.

---

## 4. Design judgment

**Must be right now (one-way doors):**
- The `script_nodes` **schema and the `is_corpus` + `level` sort key** — everything queries it; changing it after the corpus is loaded means re-running the whole ETL.
- **Embedding model + dimension** — must match between corpus load and runtime query, and between corpus and uploaded drafts. Pin it once (Q4).
- **The "numbers are SQL aggregates, prose is LLM" rule** — baked into the ETL; retrofitting it means recomputing the corpus.

**At ship:**
- Read-only SQL guard, tool-call logging, the "show SQL" affordance, Gemini safety settings, `.env.example`, README, OSI license, budget alert.

**Deferred, with a seam:**
- **Draft upload** is behind the same ETL functions the corpus uses — so the seam is "call the pipeline with `is_corpus=0`." If time runs short, the demo uses a pre-loaded draft and upload is a thin add, not a rebuild.
- **Corpus size** is a parameter (N films), not a design change — grow it late if time allows.
- **HNSW/ANN index** — deferred behind exact search; if scale ever demanded it, it's an `ALTER TABLE ADD INDEX`, local change.

**Explicitly not doing:** accounts/auth, persistence, prose-quality feedback, multi-format upload beyond one, the full 1,100-script corpus. Each recorded as a non-goal so it doesn't get "helpfully" built.

**Abstraction decisions:**
| Tempting generalization | Evidence of variation | Decision | Reason |
|---|---|---|---|
| Pluggable embedding providers | 1 (Vertex, mandated) | Concrete Vertex call behind one `embed()` function | Gate 1 fails; and non-Google AI is *disqualifying*, so a second provider can never exist here |
| Pluggable vector store / "repository" layer | 1 (ClickHouse, mandated) | Direct SQL via MCP tool | Gate 1 fails; ClickHouse is the point, not an implementation detail to hide |
| Generic "narrative metric" engine | 2–3 metrics (valence, conflict, arousal) that vary together | Three concrete columns | Gates 2+4 fail — they change for the same reason and share a source; columns are simpler than a metric registry |
| Multi-format script parser framework | 1 format at ship | One parser behind `parse_script()` seam | Gate 1; add formats only with a real second format in hand |

**One-way doors, justified:**
- *Single-table corpus+draft* over two tables: chosen because the winning query ("my draft vs. the field") is then one partition-pruned scan with identical shape for both sides — which is exactly the ClickHouse capability the (ClickHouse-engineer) judges reward. Reversal: split later is mechanical but would break the "one query, one table" pitch.
- *Exact `cosineDistance`, no ANN*: chosen because at ≤~500k vectors it's fast, exact, simpler, and dodges the documented HNSW latency/accuracy caveats. Reversal: adding an index is a local, non-breaking change.

**Decision records:**
> **Decision:** Score scene valence/conflict with the NRC VAD lexicon (deterministic), not an LLM.
> **Context:** ~12k–35k corpus scenes; part-time, ~$0 budget; invariant that parent numbers must not drift.
> **Alternatives:** *Gemini per-scene scoring* — lost on cost (thousands of calls), time (rate limits), and non-determinism (violates the no-drift invariant, and re-runs give different corpora). *Fine-tuned classifier* — lost on time to build/validate.
> **Consequences:** Corpus scoring becomes instant, free, reproducible, and defensible against "where did this number come from." Harder: lexicon is coarser than an LLM read — accepted, because *comparative percentile* framing tolerates coarse absolute values (both sides scored identically).

> **Decision:** Build agents natively with ADK on Agent Engine; ClickHouse via its MCP server.
> **Context:** Track mandates runtime ClickHouse-via-MCP and Google-only AI; judges reward deep, legible integration.
> **Alternatives:** *LangChain/custom wrapper* — lost: the resources guide explicitly recommends native ADK, and wrappers obscure the integration the judges are scoring. *Direct ClickHouse client, skip MCP* — **disqualifying** (MCP at runtime is required).
> **Consequences:** Easy: serverless deploy, clean architecture diagram, meets both hard rules. Harder: ADK is the least-familiar surface — retired first, in Slice 1.

---

## 5. Risks and failure modes

| Risk | Likelihood | Impact | Mitigation / early signal |
|---|---|---|---|
| ClickHouse MCP ↔ ADK tool integration doesn't work as imagined | Med | **Fatal** (it's the required runtime path) | **Slice 1 is built to test exactly this first**, on 10 hand-loaded rows. Early signal = skeleton query fails. |
| Corpus dataset unavailable / unlicensed / filthy | Med | High (weakens the percentile claim) | Slice 2 opens with a timeboxed data spike; fallback = hand-curated 30–50 scripts. |
| ETL scope balloons and eats all evening-time | High | High | Right-size N (Q3); pipeline is idempotent + resumable; corpus size is a dial, product works at N=50. |
| Frontend computes analytics client-side → Stage-1 disqualifier | Med | **Fatal** | Architecture forbids it; "show SQL" affordance makes violations visible; acceptance criterion checks a query fires on brush. |
| Percentile claims on thin cohorts look fake | Med | Med (hurts "Impact"/credibility) | N≥min invariant; UI degrades to "insufficient corpus" honestly. |
| Draft upload parsing fails on real formats | Med | Med | Support one clean format; pre-load a demo draft so the demo never depends on live upload. |
| Trial credits exhausted / accidental spend | Low | Med | $50 GCP alert; scale ClickHouse to zero when idle; NRC scoring removes the big LLM cost. |
| Non-Google AI sneaks in via a dependency | Low | **Fatal** | Dependency review before submit; keep AI calls to Vertex only. |

**Blast radius:** a wrong schema invalidates the whole corpus load. Everything else is local.
**Worst realistic failure:** day 14, the MCP tool turns out to need an unsupported auth/transport against Agent Engine. Detected in Slice 1 (day 1–2), which is the entire reason Slice 1 exists and is first.

---

## 6. Implementation slices

Ordered by risk. Each is end-to-end and independently demo-able. Times are rough evening-budget estimates.

### Slice 1 — Walking skeleton: prove the required spine end-to-end *(riskiest first)*
- **Intent:** A deployed Next.js page sends a question → ADK agent on Agent Engine → ClickHouse MCP tool runs a real `SELECT` against ClickHouse Cloud (~10 hand-inserted `script_nodes` rows) → a number renders in the UI. Nothing else.
- **Changes:** `infra/` (ClickHouse Cloud service, GCP project, Secret Manager); `agent/` (ADK agent + `run_scoped_sql` MCP tool, read-only guard); `web/` (one page, one input, one result); deploy configs.
- **Acceptance:** Public URL returns a live-queried value; tool-call log shows the SQL. Kill the ClickHouse service → UI shows the honest error, not a fake number.
- **Verify:** `curl` the agent endpoint with a test question → response contains the DB value + `sql_shown`; check Agent Engine logs for the tool call.
- **Rollback:** Tear down cloud resources; no data to lose.
- **Risk retired:** The single fatal integration (ADK↔MCP↔ClickHouse↔deploy). *If this can't be made to work, the track choice itself is reconsidered — which is why it's day 1.*

### Slice 2 — Corpus ETL for a right-sized N, loaded and queryable
- **Intent:** A real corpus (N per Q3) of produced films exists in `script_nodes` as full trees: scenes scored (NRC), embedded (Vertex), parents = SQL aggregates, prose summaries generated.
- **Changes:** `etl/` — `acquire` (dataset spike first), `parse_script()` (→ scenes + 4 elements), `build_tree()` (scene→sequence→act→film), `score_valence()` (NRC VAD), `embed()` (Vertex), `aggregate_parents()` (SQL), `summarize()` (Gemini, prose only), `load()` (idempotent insert `is_corpus=1`). Resumable/checkpointed.
- **Acceptance:** Row counts match expected tree math; a spot-checked film's arc looks sane; parent `valence` equals `AVG(child valence)` (invariant test); re-running ETL doesn't duplicate rows.
- **Verify:** SQL asserts: `parent.valence ≈ AVG(children.valence)`; `COUNT` per level; no orphan `parent_id`; embedding dim constant.
- **Rollback:** `TRUNCATE`/reload is cheap and idempotent.
- **Risk retired:** Data availability + quality + the no-drift invariant.

### Slice 3 — Comparative percentile query layer + `similar_scenes`
- **Intent:** The differentiating queries work: given any corpus scene, return its valence/conflict **percentile** vs. same-position-bucket + same-genre cohort (with cohort N), and its k nearest scenes via **filter-first exact `cosineDistance`**.
- **Changes:** `agent/tools/` — `scene_percentiles`, `similar_scenes`; enforce N≥min → "insufficient corpus".
- **Acceptance:** Percentiles are in [0,1] and monotonic on sorted inputs; filter-first is visible in the SQL (WHERE before ORDER BY cosineDistance); thin cohort returns the honest fallback.
- **Verify:** Unit-check percentile math against a hand-computed cohort; `EXPLAIN`/log shows filter precedes vector scan; latency < budget.
- **Rollback:** Tools are additive.
- **Risk retired:** "Is the comparative claim real and fast?" — the core of the pitch.

### Slice 4 — Interactive structural/emotional map (SQL-backed drill-down + brushing)
- **Intent:** The winning visual: an arc for a pre-loaded draft; click drills film→act→sequence→scene (each level = a query at that `level`); brushing a region fires a scoped query; "show SQL" reveals it.
- **Changes:** `web/` — arc chart (visx/d3), drill state = `level`, brush handler → `arc()`/scoped query, SQL panel.
- **Acceptance:** Each interaction issues a network→agent→SQL round-trip (observable); no client-side analytics; keyboard-navigable.
- **Verify:** Network log shows a query per brush/drill; disabling the backend blanks the chart (proving it's not client-computed).
- **Rollback:** UI-only; revert component.
- **Risk retired:** Design criterion + the "every pixel is a query" disqualifier guard.

### Slice 5 — Natural-language agent over the tools
- **Intent:** "Which of my scenes are structurally unusual, and compared to what?" → agent picks tools, runs SQL, answers in prose with named scenes + percentiles, and drives the chart selection.
- **Changes:** `agent/` — intent routing, answer composition strictly from returned rows, wire `sql_shown`/`data` to UI.
- **Acceptance:** Answers cite specific scenes + percentile positions; every claimed number appears in `sql_shown`; no number without a query.
- **Verify:** Ask the 5 canonical demo questions; assert each answer's numbers match its shown SQL's output.
- **Rollback:** Falls back to Slice 4's direct interactions.
- **Risk retired:** The "agentic" story + Quality-of-Idea articulation.

### Slice 6 — User draft upload (completes the loop)
- **Intent:** Upload one screenplay format → same ETL with `is_corpus=0` → analyzed against the corpus live.
- **Changes:** `web/` upload; `agent|etl/` on-demand pipeline reuse with `is_corpus=0`, session-scoped `script_id`.
- **Acceptance:** Uploaded draft appears as an arc and gets real percentiles vs. corpus; session cleanup removes draft rows.
- **Verify:** Upload a known test script → rows with `is_corpus=0`; percentiles computed against `is_corpus=1` only.
- **Rollback:** Feature-flag off; demo uses the pre-loaded draft.
- **Risk retired:** End-to-end product completeness. *If time is tight, this is the first slice to demo-script rather than fully build — pre-loaded draft still satisfies most acceptance criteria.*

### Slice 7 — Submission hardening + demo
- **Intent:** Meet every submission gate and make the 3-minute video.
- **Changes:** README (arch diagram, runtime instructions), OSI `LICENSE` (MIT), `.env.example`, Secret Manager wired, Gemini safety settings on, budget alert, dependency review (no non-Google AI), record + edit ≤3-min video (problem → user → live demo showing SQL → architecture flash).
- **Acceptance:** A stranger can clone, follow README, and run it; video is public + subtitled; Devpost form complete before Sept 7.
- **Verify:** Fresh-clone dry run; checklist against Section 0 rules.
- **Risk retired:** Disqualification risk.

**Slice-to-runway map (part-time, ~3 wks):** S1 by ~day 2 · S2 by ~day 6 · S3 by ~day 9 · S4 by ~day 13 · S5 by ~day 16 · S6 by ~day 18 · S7 by ~day 20, submit day 21 with buffer. **A complete, demo-able product exists after S4 (~day 13)**; S5–S6 deepen it; S7 is non-optional polish.

---

## 7. Verification

**Test strategy:**
| What | Level | Why this level |
|---|---|---|
| Percentile & aggregate math | Unit | Pure logic; wrong numbers destroy the pitch |
| Parent = AVG(children) invariant | Integration (real ClickHouse) | The no-drift guarantee lives in SQL |
| Filter-first vector search | Integration | Correctness + latency are DB behaviors |
| Agent number ↔ shown SQL match | Integration/E2E | The anti-fabrication invariant |
| 5 canonical demo questions | E2E | The actual thing judges see |

**Edge cases:** empty/thin cohort (→ honest fallback); a scene with no NRC-scorable words; a draft that fails to parse; MCP/cluster unreachable (→ error, never a fake number); duplicate ETL run (idempotent); largest realistic script.

**Non-functional:** interactive query < ~500ms P95; no non-Google AI dependency; embedding dim constant across corpus + drafts.

---

## 8. Rollout

Hackathon, single environment — no staged rollout. "Rollout" = **the submission checklist** (Section 0 + Slice 7). **Migration order** applies only to the schema: finalize `script_nodes` (Slice 1) *before* loading the corpus (Slice 2); a schema change after Slice 2 forces a full reload. **Rollback** for any slice: cloud resources are disposable; corpus reload is idempotent; there is no production data to protect. **Monitoring:** the tool-call/SQL log is the single pane that proves runtime ClickHouse usage — keep it, it doubles as demo evidence.

## 9. Stop-and-ask triggers

Stop and ask rather than decide alone if:
- The ClickHouse MCP server **cannot** be driven as an ADK tool against Agent Engine (Slice 1 fails) — this challenges the track choice; escalate before burning days.
- No usable/licensed parsed corpus is found in the Slice-2 spike — decide N and source together.
- The schema needs a change **after** corpus load — quantify reload cost first.
- Any AI call would touch a non-Google provider — never do it silently; it's disqualifying.
- Exact vector search misses the latency budget — confirm before reaching for an ANN index.
- An acceptance criterion turns out untestable as written.

## 10. Open questions

| # | Question | Owner | Blocks? | Default if unanswered |
|---|---|---|---|---|
| Q1 | Which parsed screenplay dataset (ScriptBase / ScreenPy / pre-parsed IMSDb) — and is its license OK for this submission? | User + Slice-2 spike | Blocks Slice 2 | Hand-curated 30–50 public scripts |
| Q2 | Exact transport/auth for ClickHouse MCP ↔ ADK on Agent Engine | Slice-1 spike | Blocks Slice 1 | Prove locally first, then port to Agent Engine |
| Q3 | Corpus N and genre spread (drives percentile credibility vs. ETL time) | User | Blocks Slice 2 scope | 100–150 films, ≥3 genres, ≥25/genre-position cohort |
| Q4 | Vertex embedding model + dimension to pin | Implementor | Blocks Slices 1–3 | Latest Vertex `text-embedding` model, its native dim, pinned in config |
| Q5 | Minimum cohort N to emit a percentile (else "insufficient corpus") | User | Non-blocking | 20 |
| Q6 | Which single upload format to support first | User | Blocks Slice 6 | Fountain / `.txt` (simplest to parse) |

## 11. Out-of-scope follow-ups

Grow corpus to full IMSDb; add ANN index if scale demands; multi-format upload; accounts + saved drafts; character-arc view (per-`char_id` trajectories); export coverage PDF for the dev-exec buyer; LLM-assisted (but SQL-verified) narrative suggestions.

---

## Residual risk (honest)

The concept is well-targeted and the two scariest technical risks are deliberately front-loaded (S1 integration, S2 data). The real residual risk is **time, not feasibility**: at 2–3 hrs/day, S1–S4 must stay disciplined so a complete product exists by ~day 13. The most likely *bad* outcome is not failure but a thinner corpus and a demo-scripted upload — both of which still clear the acceptance bar because the architecture, the runtime ClickHouse story, and the comparative-percentile insight (the parts judges actually score) survive intact. Nothing here claims zero risk; the plan is structured so that when time slips, it slips into scope (corpus size, live upload) and never into the disqualifiers (Google-only AI, runtime ClickHouse-via-MCP, public repo/URL/video).
