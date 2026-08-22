# Agentic Cinema — Build Progress Tracker

> **Living document. Update at the end of every working session.**
> This tracks *state*: what's done, where we are, what's pending in code + workflow.
> The *spec* lives in [`docs/plans/agentic-cinema-screenplay-map.md`](../docs/plans/agentic-cinema-screenplay-map.md) — read it for the "why" behind any decision.

---

## 🎯 At a glance

| | |
|---|---|
| **Product** | ClickHouse-native agent: interactive structural/emotional map of a screenwriter's draft, with percentile comparison vs. a produced-film corpus |
| **Track** | ClickHouse · **AI = Google only** (Vertex/Gemini) · **ClickHouse queried at runtime via MCP** |
| **Deadline** | **Submit by Sept 7, 2026, 2:00pm PT** (site's Sept 9 is unverified — don't trust it) |
| **Runway** | ~17 days from 2026-08-21, part-time ~2–3 hrs/day |
| **Current phase** | ✅ **Slice 1 — Walking skeleton COMPLETE** (live round-trip verified end-to-end, locally) → next: Slice 2 |
| **Overall status** | 🟢 Building — fatal integration risk retired with real evidence. Not yet cloud-deployed (still local). |

---

## 🚦 Slice status board

Legend: ⬜ not started · 🟳 in progress · ✅ done · ⏭️ deferred/demo-scripted

| # | Slice | Status | Retires the risk of… | Target |
|---|---|---|---|---|
| 1 | Walking skeleton (ADK↔MCP↔ClickHouse↔deploy, 13 rows) | ✅* | *The fatal integration* | Day 2 |
| 2 | Corpus ETL (parsed dataset → tree → NRC score → embed → load) | ⬜ | Data availability + no-drift | Day 5 |
| 3 | Percentile + filter-first vector query layer | ⬜ | "Is the comparative claim real & fast?" | Day 8 |
| 4 | Interactive map UI (SQL-backed drill-down + brush) | ⬜ | Design + "every pixel is a query" | Day 11 ← *complete product* |
| 5 | Natural-language agent over the tools | ⬜ | The agentic story | Day 13 |
| 6 | User draft upload (`is_corpus=0`) | ⬜ | End-to-end completeness | Day 15 |
| 7 | Hardening + demo video + submission | ⬜ | Disqualifiers | Day 17, submit |

**Milestone:** a complete, demo-able product exists after **Slice 4**. Slices 5–6 deepen it; Slice 7 is non-optional.
*Slice 1 = ✅ locally (real live queries verified); ⬜ cloud deploy (Agent Engine/Cloud Run) still pending — can happen anytime before Slice 7, not blocking Slice 2+.

---

## 📍 Where we are right now

**Last session:** 2026-08-22 (Session 4 — Slice 1 live verification, COMPLETE)
**Done so far:** Slice 1 fully verified live — real questions, real ClickHouse queries, real Gemini/Vertex answers, through both the agent directly and the Next.js UI's actual API route. Found and fixed 4 real bugs (see Session 4 log). Both dev servers are running right now: agent on **localhost:8000**, web UI on **localhost:3000** — open the UI in a browser to see it live.
**Next action:** either (a) deploy to Cloud Run/Agent Engine for a public URL, or (b) move on to **Slice 2 (corpus ETL)** — resolve Q1 (dataset choice) first. Deploy is not blocking Slice 2; can be done anytime before Slice 7.
**Blocked on:** nothing. All Slice-1 blockers are cleared.

**IMMEDIATE NEXT STEP (start of next session):**
1. If servers aren't still running: restart with `cd agent && uv run uvicorn server:app --port 8000` and `cd web && npm run dev`, then open http://localhost:3000.
2. Decide: deploy now, or move to Slice 2. Recommend Slice 2 first (deploy is mechanical; corpus is the real remaining unknown) — start with the **Q1 spike**: check ScriptBase / ScreenPy / pre-parsed IMSDb for license + quality.
3. Still pending, non-blocking: $50 GCP budget alert (manual, Console), create public GitHub repo, gcloud CLI's own stale-token quirk (see Session 4 log — doesn't affect the app, only `gcloud` commands like `projects describe`).

---

## 🔧 Environment / setup state

| Item | Status | Notes |
|---|---|---|
| Google Cloud account + $300 credits | ✅ | **Switched accounts Session 3** — now on `ajaye5016@gmail.com` (original `ajayelika9010@gmail.com`'s trial was suspected exhausted). Fresh trial active. |
| GCP project | ✅ | **`project-7acae5d3-1b92-4913-971`** ("agent-cinema") — billing confirmed enabled (`billingAccounts/01AB80-1B840F-391D4E`) |
| APIs enabled (Vertex AI, Cloud Run, Secret Manager) | ✅ | Enabled on the new project Session 3 |
| `gcloud` CLI authenticated | ✅ | Active account = `ajaye5016@gmail.com`; ADC quota project set to `project-7acae5d3-1b92-4913-971` |
| ClickHouse Cloud trial ($300/30-day) | ✅ | Service created, schema + 10-row seed loaded (user confirmed Session 3) |
| ClickHouse host/password | ✅ | In `agent/.env` (port **8443**, verified working live) |
| ClickHouse MCP server reachable | ✅ | Verified live via `uvx mcp-clickhouse`, real queries + real answers |
| `uv` on PATH (for `uvx mcp-clickhouse`) | ✅ | uv 0.9.30 present |
| $50 GCP budget alert set | ⬜ | Manual step in Console → Billing → Budgets & alerts (CLI needs an extra API + notification setup, deferred) |
| Repo scaffold (`agent/ web/ etl/ infra/`) | ✅ | Done Session 2 |
| MIT LICENSE + .gitignore | ✅ | Done Session 2 |
| Public GitHub repo | ⬜ | Not yet created/committed (Slice 7; can do early) |

---

## 📋 Pending work — code & workflow (detailed)

### Slice 1 — Walking skeleton ✅ (local) / ⬜ (cloud deploy)
**Code**
- [x] Repo scaffold: `agent/`, `web/`, `etl/`, `infra/`, root README, LICENSE, .gitignore
- [x] ClickHouse `script_nodes` DDL → `infra/clickhouse/schema.sql`
- [x] 13-row seed (all 4 tree levels) → `infra/clickhouse/seed.sql` — **corrected mid-session**, see below
- [x] ADK agent using the ClickHouse MCP server's **actual** tool name `run_query` via MCPToolset (read-only by design — `CLICKHOUSE_ALLOW_WRITE_ACCESS` never set) — *deviation from plan's custom `run_scoped_sql`, kept*
- [x] Next.js one page + `/api/ask` proxy; renders answer + **"show SQL"** + raw data
- [x] FastAPI adapter (`server.py`) shaping `{answer, sql_shown, data}` — runs locally, deployable to Cloud Run
- [x] `.env.example` for agent + web; secrets kept out of repo; `.env`/`.env.local` populated and working
- [x] `python-dotenv` loads `.env` at process start (was missing — see bugs below)
- [x] Applied schema + corrected seed to the live ClickHouse Cloud service
- [ ] Deploy agent (Agent Engine or Cloud Run) + web (Cloud Run/Vercel) — **still local only**
- [ ] Secrets in Secret Manager *(at deploy)*

**Workflow / verify**
- [x] Offline unit tests for the `{answer, sql_shown, data}` parser — **4/4 pass**
- [x] Web build + typecheck clean (`npm run build`)
- [x] Agent + server modules import & construct (`LlmAgent` + `MCPToolset`, Runner + routes)
- [x] **Live, real queries verified** (both agent-direct and through the Next.js `/api/ask` proxy):
  - "average conflict of the scenes" → 0.61, correct, `sql_shown` populated
  - "lowest valence scene" → "INT. LAB - DAWN" -0.32, correct
  - "how many scenes in each act" → 2/2/2 across 3 acts, correct, after two real bugs fixed (below)
- [x] Honest-failure behavior **observed for real** (not simulated): a ClickHouse Cloud cold-start timeout caused a genuine failure, and the agent said "couldn't retrieve the data" rather than fabricating a number — the core anti-fabrication invariant holds under a real failure, not just a designed test
- [ ] Public URL loads end-to-end *(needs deploy — not done this session)*

**Risk retired:** the whole spine round-trips live, verified with real evidence, twice, through both the agent directly and the actual browser-facing API route.

### Slice 2 — Corpus ETL ⬜
- [ ] **Spike (do first):** confirm parsed dataset + license (Q1) — ScriptBase / ScreenPy / pre-parsed IMSDb
- [ ] `parse_script()` → scenes + 4 elements
- [ ] `build_tree()` scene→sequence→act→film
- [ ] `score_valence()` via NRC VAD lexicon (deterministic)
- [ ] `embed()` via Vertex text-embedding (pin model + dim — Q4)
- [ ] `aggregate_parents()` — numbers = SQL AVG/SUM (never LLM)
- [ ] `summarize()` — Gemini, prose only
- [ ] `load()` idempotent insert, `is_corpus=1`
- [ ] Load N≈100–150 films (Q3)
- [ ] Verify: `parent.valence ≈ AVG(children)`, counts per level, no orphans, constant embedding dim

### Slice 3 — Query layer ⬜
- [ ] `scene_percentiles` tool (position-bucket + genre cohort, returns percentile + cohort N)
- [ ] `similar_scenes` tool (filter-first WHERE, then exact `cosineDistance` LIMIT k)
- [ ] N≥min guard → "insufficient corpus" (Q5, default 20)
- [ ] Verify: percentiles in [0,1] & monotonic; filter precedes vector scan in logged SQL; latency < ~500ms P95

### Slice 4 — Interactive map UI ⬜
- [ ] Arc chart (visx/d3) for a pre-loaded draft
- [ ] Drill film→act→sequence→scene = query at that `level`
- [ ] Brush region → scoped query (**not** client-side filter)
- [ ] "Show SQL" panel
- [ ] Verify: every interaction fires a query; backend off → chart blanks (proves not client-computed); keyboard-navigable

### Slice 5 — NL agent ⬜
- [ ] Intent routing → tool selection
- [ ] Answer composed strictly from returned rows; every number appears in `sql_shown`
- [ ] Wire `sql_shown` + `data` to UI; agent drives chart selection
- [ ] Verify: 5 canonical demo questions; each answer's numbers match its shown SQL

### Slice 6 — Draft upload ⬜
- [ ] Upload one format (Q6, default Fountain/`.txt`)
- [ ] Reuse ETL with `is_corpus=0`, session-scoped `script_id`
- [ ] Compare draft vs. `is_corpus=1` corpus
- [ ] Session cleanup removes draft rows
- [ ] ⏭️ *If time-tight: demo-script with a pre-loaded draft instead*

### Slice 7 — Hardening + demo ⬜
- [ ] README (arch diagram + runtime instructions)
- [ ] MIT `LICENSE`, `.env.example`
- [ ] Gemini safety settings on
- [ ] Dependency review — **no non-Google AI** (disqualifying)
- [ ] Fresh-clone dry run
- [ ] ≤3-min video: problem → user → live demo *showing SQL* → architecture flash
- [ ] Devpost submission form complete (hosted URL, repo, video, track) **before Sept 7**

---

## ⚠️ Open questions still blocking (from plan §10)

| # | Question | Blocks | Default if unanswered |
|---|---|---|---|
| Q1 | Which parsed screenplay dataset + license OK? | Slice 2 | Hand-curated 30–50 public scripts |
| Q2 | ClickHouse MCP ↔ ADK transport/auth on Agent Engine | Slice 1 | Prove locally, then port |
| Q3 | Corpus N + genre spread | Slice 2 scope | 100–150 films, ≥25/cohort |
| Q4 | Vertex embedding model + dim to pin | Slices 1–3 | Latest Vertex `text-embedding`, native dim |
| Q5 | Min cohort N to emit a percentile | non-blocking | 20 |
| Q6 | First upload format | Slice 6 | Fountain / `.txt` |

---

## 🚫 Guardrails (never violate — these lose the whole submission)

1. **All AI = Google Cloud (Vertex/Gemini).** No AWS/Azure/OpenAI/Anthropic in the AI path.
2. **ClickHouse queried at runtime via its MCP server.** Passive file-store = Stage-1 fail.
3. **Every displayed number comes from a live SQL query.** No client-side analytics on cached JSON.
4. **Numbers = SQL aggregates; LLM only for prose + embeddings.** No LLM-guessed numbers.
5. **Public repo + OSI license + deployed URL + ≤3-min public video** before the deadline.

---

## 🗒️ Session log

*(Newest first. Each session: what changed, decisions, what's next.)*

### Session 4 — 2026-08-22 — Slice 1 live verification (COMPLETE) — 4 real bugs found & fixed
Picked up with `.env` filled in by the user. Found and fixed, in order:

1. **`.env` was never loaded into the process at all.** `config.py`/`server.py` only used `os.getenv()`, and nothing called a dotenv loader — so every `.env` value (ClickHouse creds, GCP project, the Vertex flag) had been silently ineffective since Slice 1 was first written. **Fix:** added `python-dotenv`; `load_dotenv()` now runs at the top of `server.py` (before the agent module imports, since `agent.py` builds `root_agent` at import time) and again in `config.py` for any other future entrypoint (ETL, deploy scripts).
2. **`.env` had `GOOGLE_GENAI_USE_VERTEXAI=FALSE` plus a `GOOGLE_API_KEY`** — someone had worked around an earlier auth error by switching to the direct Gemini API (AI Studio) instead of fixing Vertex auth. This silently violates the hackathon's hard "Google Cloud/Vertex AI only" rule. **Fix:** flipped to `TRUE`, removed the API key — auth now goes through ADC (already confirmed working) as designed.
3. **The `project-7acae5d3-1b92-4913-971` GCP project turned out to be an AI-Studio-auto-provisioned project**, not a normal Console project — `gcloud projects describe`/`services list` gave permission-denied for it under the CLI's own token even though `services enable` had worked earlier. Root cause turned out to be a **separate, real gcloud bug**: `gcloud config` reported the active account as `ajaye5016@gmail.com`, but the actual CLI OAuth token resolved to the **old** account `ajayelika9010@gmail.com` (confirmed via `/oauth2/v1/userinfo`). This is a `gcloud` CLI credential-cache quirk, **not an ADC problem** — verified ADC independently resolves correctly to `ajaye5016@gmail.com`, and a direct `curl` to the Vertex AI `generateContent` endpoint using the ADC token **succeeded** ("OK" response). So: the app works fine; only ad-hoc `gcloud` CLI introspection commands on this project are unreliable. Non-blocking, left as a known quirk — fixable later with `gcloud auth revoke` + clean re-login if it ever matters.
4. **Wrong ClickHouse MCP tool name.** `events.py`/`agent.py` assumed the tool was called `run_select_query` (a guess from documentation), but the actual installed `mcp-clickhouse` package registers it as **`run_query`** (confirmed by reading its source in the `uvx` ephemeral cache: `Tool.from_function(run_query_async, name="run_query")`, arg name `query`, read-only unless `CLICKHOUSE_ALLOW_WRITE_ACCESS` is set — which we never set). This silently broke the `sql_shown`/`data` "show your work" contract even though queries were actually running correctly. **Fix:** corrected the constant in `events.py`, the instruction text in `agent.py`, and the test fixtures.

Also found and fixed two **data/prompt correctness bugs** via live testing (not integration bugs — the pipe worked, the content was wrong):

5. **Seed data violated the schema's own tree invariant.** `seed.sql` had scenes pointing directly at acts, skipping the `sequence` (level 1) tier the schema declares — so a natural 3-hop scene→sequence→act join the model correctly attempted returned zero rows. **Fix:** rewrote `seed.sql` to properly populate all 4 levels (13 rows: 1 film → 3 acts → 3 sequences → 6 scenes), reloaded live via ClickHouse's HTTP interface (`TRUNCATE` + `INSERT`, comments stripped — ClickHouse's `VALUES` parser chokes on inline `--` comments between tuples). Spot-verified the parent-equals-`AVG(children)` invariant holds exactly on the reloaded data.
6. **Agent's hand-written schema instruction was incomplete/wrong**, causing two follow-on mistakes: (a) it omitted `parent_id`/`node_id`, so the model initially claimed no parent-child relationship existed at all; (b) after that was fixed, the model grouped an aggregate query by `slug` (correct for scenes, but scenes-only — empty at higher levels) which silently merged 3 distinct acts into one bucket. **Fix:** added `parent_id`/`node_id` to the instruction, added a `list_tables`-first fallback for schema drift, and an explicit "group by `node_id` not `slug` above scene level" rule.

**End state, verified with real evidence (not assumed):** three distinct live questions, asked through *both* the agent directly and the actual Next.js `/api/ask` route the browser UI calls, all correct: avg conflict (0.61), lowest-valence scene ("INT. LAB - DAWN"), and scenes-per-act (2/2/2 across 3 acts) — each with `sql_shown` populated with the real SQL Gemini wrote. Also observed a **genuine** (not staged) ClickHouse Cloud cold-start timeout, where the agent correctly reported "couldn't retrieve the data" instead of fabricating a number — the core anti-fabrication design invariant held under a real failure.
**Both dev servers left running:** agent on `localhost:8000`, web on `localhost:3000`.
**Not done this session:** cloud deployment (Cloud Run/Agent Engine) — app is fully verified but still local-only.

### Session 3 — 2026-08-21 — Cloud provisioning
- **ClickHouse Cloud:** service created (user chose 1 replica, min 16GiB/4vCPU, max capped ~32GiB/8vCPU to limit runaway autoscale cost, TDE off, crash reports off). Schema (`infra/clickhouse/schema.sql`) and 10-row seed (`seed.sql`) applied via the Cloud SQL console — user confirmed success.
- **GCP account switch:** original account `ajayelika9010@gmail.com`'s trial status was uncertain (user suspected exhausted; `gcloud billing accounts describe` only confirmed `open: true`, couldn't get exact balance via CLI — that's Console-only). Rather than risk it, reauthenticated to a **new** account `ajaye5016@gmail.com` with commands run by the user directly in their terminal (`gcloud auth application-default revoke`, `gcloud auth login`, `gcloud auth application-default login`).
- New project **`project-7acae5d3-1b92-4913-971`** ("agent-cinema") already existed under the new account with billing enabled. Set as active project; ADC quota project set to match; Vertex AI + Cloud Run + Secret Manager APIs enabled and verified.
- **Corrected a bug found this session:** ClickHouse connection port in `.env.example`/`config.py` was wrong — was `9440` (native `clickhouse-client` CLI port) but `mcp-clickhouse`/`clickhouse-connect` (what our agent actually uses) needs the **HTTPS port `8443`**. Fixed in both files.
- **Not yet done:** ClickHouse host/password haven't been entered into `agent/.env` yet — that's the one remaining blocker before the Slice-1 live smoke test.
- **Next:** see "IMMEDIATE NEXT STEP" above.

### Session 2 — 2026-08-21 — Slice 1 build (walking skeleton)
- Scaffolded repo: `infra/clickhouse/` (schema + 10-row seed), `agent/` (ADK + FastAPI), `web/` (Next.js), `etl/` stub, root README/LICENSE/.gitignore.
- **Verified offline:** 4/4 unit tests pass (event→`{answer,sql_shown,data}` parser); `npm run build` clean; agent + server modules import & construct (`LlmAgent` + `MCPToolset`, Runner + `/ask` `/health` routes).
- **Deviation:** used the ClickHouse MCP server's native `run_select_query` (read-only) via ADK `MCPToolset` instead of a custom `run_scoped_sql` tool — more faithful to the "runtime via MCP" requirement, less custom code. SQL captured from tool-call events for the "show SQL" affordance.
- **Real conflict resolved:** `google-adk` needs `mcp>=1.24,<2`; `mcp-clickhouse` needs `mcp 2`/`fastmcp`. Fix = run the ClickHouse MCP **server** as an isolated `uvx mcp-clickhouse` subprocess; agent env pinned `mcp<2`. Also moved deprecated `StdioServerParameters` → `StdioConnectionParams`.
- **Pending (needs creds):** live round-trip (uvx server → ClickHouse Cloud → Gemini answer), and deploy. Model default `gemini-2.5-flash` (env-configurable) — verify availability on your Vertex project/region.
- **Next:** user provisions ClickHouse Cloud + `gcloud` auth; then apply schema+seed and run the live smoke test.

### Session 1 — 2026-08-21 — Planning
- Researched hackathon (rules, prizes, judging, tracks). Chose ClickHouse track.
- Locked product concept, architecture, and all technical decisions.
- Wrote full plan → `docs/plans/agentic-cinema-screenplay-map.md`.
- Confirmed Google Cloud $300 credits obtained.
- Created this tracker.
- **Next:** provision GCP + ClickHouse Cloud; scaffold repo; build Slice 1.
