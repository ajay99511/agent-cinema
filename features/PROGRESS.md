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
| **Current phase** | 🟳 **Slice 1 — Walking skeleton** (code done + offline-verified; live round-trip pending creds) |
| **Overall status** | 🟢 Building — Slice 1 code complete, blocked only on cloud creds for live verify |

---

## 🚦 Slice status board

Legend: ⬜ not started · 🟳 in progress · ✅ done · ⏭️ deferred/demo-scripted

| # | Slice | Status | Retires the risk of… | Target |
|---|---|---|---|---|
| 1 | Walking skeleton (ADK↔MCP↔ClickHouse↔deploy, 10 rows) | 🟳 | *The fatal integration* | Day 2 |
| 2 | Corpus ETL (parsed dataset → tree → NRC score → embed → load) | ⬜ | Data availability + no-drift | Day 5 |
| 3 | Percentile + filter-first vector query layer | ⬜ | "Is the comparative claim real & fast?" | Day 8 |
| 4 | Interactive map UI (SQL-backed drill-down + brush) | ⬜ | Design + "every pixel is a query" | Day 11 ← *complete product* |
| 5 | Natural-language agent over the tools | ⬜ | The agentic story | Day 13 |
| 6 | User draft upload (`is_corpus=0`) | ⬜ | End-to-end completeness | Day 15 |
| 7 | Hardening + demo video + submission | ⬜ | Disqualifiers | Day 17, submit |

**Milestone:** a complete, demo-able product exists after **Slice 4**. Slices 5–6 deepen it; Slice 7 is non-optional.

---

## 📍 Where we are right now

**Last session:** 2026-08-21 (Session 3 — cloud provisioning)
**Done so far:** ClickHouse Cloud service created, schema + 10-row seed applied (user confirmed in console). Switched GCP accounts (fresh trial), new project `project-7acae5d3-1b92-4913-971` fully provisioned: billing confirmed, ADC set, Vertex AI + Cloud Run + Secret Manager APIs enabled.
**Next action:** get ClickHouse host + password into `agent/.env` (plus `GOOGLE_CLOUD_PROJECT=project-7acae5d3-1b92-4913-971`), then run the **first live query** end-to-end to finish Slice 1.
**Blocked on:** ClickHouse host + password only — everything else needed for Slice 1's live round-trip is now in place.

**IMMEDIATE NEXT STEP (start of next session):**
1. Get ClickHouse **host** + **password** from the Cloud console "Connect" screen (user has this; needs to share or fill `agent/.env` directly — copy from `agent/.env.example`).
2. Fill `agent/.env`: `CLICKHOUSE_HOST`, `CLICKHOUSE_PASSWORD`, `GOOGLE_CLOUD_PROJECT=project-7acae5d3-1b92-4913-971`, `GOOGLE_CLOUD_LOCATION=us-central1`.
3. Run: `cd agent && uv run uvicorn server:app --reload --port 8080` (venv + deps already installed from Session 2 — `agent/.venv` exists).
4. Smoke test: `curl -s localhost:8080/ask -H "content-type: application/json" -d "{\"message\":\"What is the average conflict of the scenes?\"}"` → expect an answer + `sql_shown` containing a real SELECT.
5. If it works → Slice 1 is DONE. Update this file, commit, move to Slice 2 (corpus ETL — first resolve Q1 dataset choice).
6. Also still pending: $50 GCP budget alert (manual, Console), create public GitHub repo.

---

## 🔧 Environment / setup state

| Item | Status | Notes |
|---|---|---|
| Google Cloud account + $300 credits | ✅ | **Switched accounts Session 3** — now on `ajaye5016@gmail.com` (original `ajayelika9010@gmail.com`'s trial was suspected exhausted). Fresh trial active. |
| GCP project | ✅ | **`project-7acae5d3-1b92-4913-971`** ("agent-cinema") — billing confirmed enabled (`billingAccounts/01AB80-1B840F-391D4E`) |
| APIs enabled (Vertex AI, Cloud Run, Secret Manager) | ✅ | Enabled on the new project Session 3 |
| `gcloud` CLI authenticated | ✅ | Active account = `ajaye5016@gmail.com`; ADC quota project set to `project-7acae5d3-1b92-4913-971` |
| ClickHouse Cloud trial ($300/30-day) | ✅ | Service created, schema + 10-row seed loaded (user confirmed Session 3) |
| ClickHouse host/password | ⬜ | **Not yet shared with agent** — needed to fill `agent/.env` |
| ClickHouse MCP server reachable | ⬜ | Verified when live round-trip runs |
| `uv` on PATH (for `uvx mcp-clickhouse`) | ✅ | uv 0.9.30 present |
| $50 GCP budget alert set | ⬜ | Manual step in Console → Billing → Budgets & alerts (CLI needs an extra API + notification setup, deferred) |
| Repo scaffold (`agent/ web/ etl/ infra/`) | ✅ | Done Session 2 |
| MIT LICENSE + .gitignore | ✅ | Done Session 2 |
| Public GitHub repo | ⬜ | Not yet created/committed (Slice 7; can do early) |

---

## 📋 Pending work — code & workflow (detailed)

### Slice 1 — Walking skeleton 🟳
**Code**
- [x] Repo scaffold: `agent/`, `web/`, `etl/`, `infra/`, root README, LICENSE, .gitignore
- [x] ClickHouse `script_nodes` DDL → `infra/clickhouse/schema.sql`
- [x] 10 hand-made seed rows → `infra/clickhouse/seed.sql`
- [x] ADK agent using the **ClickHouse MCP server's native `run_select_query`** via MCPToolset (read-only by design) — *deviation from plan's custom `run_scoped_sql`, see session log*
- [x] Next.js one page + `/api/ask` proxy; renders answer + **"show SQL"** + raw data
- [x] FastAPI adapter (`server.py`) shaping `{answer, sql_shown, data}` — runs locally, deployable to Cloud Run
- [x] `.env.example` for agent + web; secrets kept out of repo
- [ ] Apply schema + seed to a live ClickHouse Cloud service *(needs creds)*
- [ ] Deploy agent (Agent Engine or Cloud Run) + web (Cloud Run/Vercel) *(needs creds)*
- [ ] Secrets in Secret Manager *(at deploy)*

**Workflow / verify**
- [x] Offline unit tests for the `{answer, sql_shown, data}` parser — **4/4 pass**
- [x] Web build + typecheck clean (`npm run build`)
- [x] Agent + server modules import & construct (`LlmAgent` + `MCPToolset`, Runner + routes)
- [ ] Live: `curl /ask` → response contains a DB value + `sql_shown` *(needs creds)*
- [ ] Kill ClickHouse → UI shows honest error, **not** a fake number *(needs creds)*
- [ ] Public URL loads end-to-end *(needs deploy)*

**Risk retired when:** the whole spine round-trips live. *Code path proven to construct; the live query is the remaining gate.*

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
