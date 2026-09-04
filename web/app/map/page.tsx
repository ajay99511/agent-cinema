"use client";

import { useEffect, useMemo, useState } from "react";

type Film = { script_id: number; title: string; genre: string; year: number };
type ArcNode = {
  node_id: number;
  seq_idx: number;
  pct_position: number;
  valence: number;
  conflict: number;
  title: string;
  slug: string;
  summary: string;
};
type ArcResponse = {
  sql?: string;
  level?: number;
  has_children?: boolean;
  nodes?: ArcNode[];
  error?: string;
  detail?: string;
};

const LEVEL_NAME = ["Scene", "Sequence", "Act", "Film"] as const;
const CHART_W = 720;
const CHART_H = 120;
const PAD = 28;

type Crumb = { level: number; parentId: number | undefined; label: string };

export default function MapPage() {
  const [films, setFilms] = useState<Film[]>([]);
  const [scriptId, setScriptId] = useState<number | null>(null);
  const [trail, setTrail] = useState<Crumb[]>([]); // breadcrumb history, root first
  const [arc, setArc] = useState<ArcResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const current = trail[trail.length - 1];

  useEffect(() => {
    fetch("/api/films")
      .then((r) => r.json())
      .then((json) => setFilms(json.films ?? []));
  }, []);

  function selectFilm(id: number) {
    setScriptId(id);
    setTrail([{ level: 2, parentId: undefined, label: "" }]);
  }

  useEffect(() => {
    if (scriptId == null || !current) return;
    setLoading(true);
    const params = new URLSearchParams({ script_id: String(scriptId), level: String(current.level) });
    if (current.parentId != null) params.set("parent_id", String(current.parentId));
    fetch(`/api/arc?${params.toString()}`)
      .then((r) => r.json())
      .then((json: ArcResponse) => {
        setArc(json);
        setHoverIdx(null);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptId, current?.level, current?.parentId]);

  function drillInto(node: ArcNode) {
    if (!arc?.has_children) return;
    const childLevel = current.level - 1;
    // Non-scene nodes have no slug (schema: slug is scene-only) — identify the clicked
    // act/sequence by its 1-based position, not by title (which is just the film name
    // repeated on every row and would make every crumb look identical).
    const label = `${LEVEL_NAME[current.level]} ${node.seq_idx + 1}`;
    setTrail([...trail, { level: childLevel, parentId: node.node_id, label }]);
  }

  function goToCrumb(i: number) {
    setTrail(trail.slice(0, i + 1));
  }

  const nodes = arc?.nodes ?? [];
  const scales = useMemo(() => makeScales(nodes), [nodes]);

  return (
    <main className="wrap" style={{ maxWidth: 820 }}>
      <h1>Structural &amp; Emotional Map</h1>
      <p className="subtitle">
        Drill film → act → sequence → scene. Every point is a live ClickHouse row — nothing here
        is computed in the browser.
      </p>

      <div className="card" style={{ marginTop: 0 }}>
        <label htmlFor="film-select" style={{ display: "block", marginBottom: 8, color: "var(--muted)" }}>
          Film
        </label>
        <select
          id="film-select"
          value={scriptId ?? ""}
          onChange={(e) => selectFilm(Number(e.target.value))}
          style={{
            width: "100%", padding: "10px 12px", background: "var(--panel)",
            border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)", fontSize: "1rem",
          }}
        >
          <option value="" disabled>
            Choose a film…
          </option>
          {films.map((f) => (
            <option key={f.script_id} value={f.script_id}>
              {f.title} ({f.year}, {f.genre})
            </option>
          ))}
        </select>
      </div>

      {scriptId != null && (
        <>
          <nav aria-label="Drill-down breadcrumb" style={{ margin: "16px 0", fontSize: "0.9rem" }}>
            {trail.map((c, i) => {
              const text = `${LEVEL_NAME[c.level]}${c.label ? `s: ${c.label}` : "s"}`;
              return (
                <span key={i}>
                  {i > 0 && <span style={{ color: "var(--muted)" }}> &rsaquo; </span>}
                  {i === trail.length - 1 ? (
                    <span>{text}</span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => goToCrumb(i)}
                      style={{ background: "none", border: 0, color: "var(--accent)", cursor: "pointer", padding: 0, font: "inherit", textDecoration: "underline" }}
                    >
                      {text}
                    </button>
                  )}
                </span>
              );
            })}
          </nav>

          {arc?.error && (
            <p className="answer error">
              Could not load this view — {arc.error}
              {arc.detail ? ` (${arc.detail})` : ""}. The chart intentionally shows nothing
              rather than stale or fake data.
            </p>
          )}

          {!arc?.error && (
            <div className="card" style={{ opacity: loading ? 0.5 : 1, transition: "opacity 120ms" }}>
              <MiniChart
                label="Valence"
                nodes={nodes}
                metric="valence"
                scales={scales}
                hoverIdx={hoverIdx}
                onHover={setHoverIdx}
                onClick={drillInto}
                clickable={!!arc?.has_children}
              />
              <div style={{ height: 18 }} />
              <MiniChart
                label="Conflict"
                nodes={nodes}
                metric="conflict"
                scales={scales}
                hoverIdx={hoverIdx}
                onHover={setHoverIdx}
                onClick={drillInto}
                clickable={!!arc?.has_children}
              />

              {hoverIdx != null && nodes[hoverIdx] && (
                <div
                  className="card"
                  style={{ marginTop: 14, background: "var(--sql-bg)", fontSize: "0.9rem" }}
                >
                  <strong>{nodes[hoverIdx].slug || nodes[hoverIdx].title}</strong>
                  <div style={{ color: "var(--muted)", margin: "4px 0" }}>{nodes[hoverIdx].summary}</div>
                  <div>
                    valence <strong>{nodes[hoverIdx].valence.toFixed(3)}</strong> · conflict{" "}
                    <strong>{nodes[hoverIdx].conflict.toFixed(3)}</strong>
                  </div>
                  {arc?.has_children && (
                    <div style={{ color: "var(--accent)", marginTop: 6 }}>Click the point to drill in →</div>
                  )}
                </div>
              )}

              {arc?.sql && (
                <details style={{ marginTop: 14 }}>
                  <summary>SQL run against ClickHouse</summary>
                  <pre>{arc.sql}</pre>
                </details>
              )}
            </div>
          )}
        </>
      )}
    </main>
  );
}

function makeScales(nodes: ArcNode[]) {
  const pad = (vals: number[]) => {
    if (vals.length === 0) return { min: 0, max: 1 };
    let min = Math.min(...vals);
    let max = Math.max(...vals);
    if (max - min < 0.02) {
      min -= 0.05;
      max += 0.05;
    }
    const span = max - min;
    return { min: min - span * 0.15, max: max + span * 0.15 };
  };
  return {
    valence: pad(nodes.map((n) => n.valence)),
    conflict: pad(nodes.map((n) => n.conflict)),
  };
}

function MiniChart({
  label, nodes, metric, scales, hoverIdx, onHover, onClick, clickable,
}: {
  label: string;
  nodes: ArcNode[];
  metric: "valence" | "conflict";
  scales: ReturnType<typeof makeScales>;
  hoverIdx: number | null;
  onHover: (i: number | null) => void;
  onClick: (node: ArcNode) => void;
  clickable: boolean;
}) {
  const { min, max } = scales[metric];
  const innerW = CHART_W - PAD * 2;
  const innerH = CHART_H - PAD * 2;

  const x = (i: number) => (nodes.length <= 1 ? innerW / 2 : (i / (nodes.length - 1)) * innerW);
  const y = (v: number) => innerH - ((v - min) / (max - min || 1)) * innerH;

  const points = nodes.map((n, i) => [x(i), y(n[metric])]);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const areaPath = points.length
    ? `${path} L${points[points.length - 1][0].toFixed(1)},${innerH} L0,${innerH} Z`
    : "";

  function nearestIndex(e: { clientX: number; target: EventTarget | null }): number | null {
    if (nodes.length === 0) return null;
    const rect = (e.target as SVGElement).ownerSVGElement!.getBoundingClientRect();
    const localX = e.clientX - rect.left - PAD;
    let nearest = 0;
    let best = Infinity;
    points.forEach((p, i) => {
      const d = Math.abs(p[0] - localX);
      if (d < best) {
        best = d;
        nearest = i;
      }
    });
    return nearest;
  }

  function handleMove(e: React.PointerEvent<SVGSVGElement>) {
    onHover(nearestIndex(e));
  }

  function handleClick(e: React.MouseEvent<SVGSVGElement>) {
    // Compute the target point directly from the click's own position rather than trusting
    // `hoverIdx` state — a fast click can fire before the preceding pointermove's setState
    // has committed, which made drill-down clicks silently no-op (found via a real headless
    // browser screenshot test, not just typecheck/build — see PROGRESS.md Slice 4 log).
    const i = nearestIndex(e);
    if (i != null && nodes[i]) onClick(nodes[i]);
  }

  return (
    <div>
      <div style={{ color: "var(--muted)", fontSize: "0.8rem", marginBottom: 4 }}>{label}</div>
      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        width="100%"
        role="img"
        aria-label={`${label} across the story, ${nodes.length} points`}
        onPointerMove={handleMove}
        onPointerLeave={() => onHover(null)}
        onClick={handleClick}
        style={{ cursor: clickable ? "pointer" : "default", display: "block" }}
      >
        <g transform={`translate(${PAD},${PAD})`}>
          <line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="var(--border)" strokeWidth={1} />
          {metric === "valence" && min < 0 && max > 0 && (
            <line
              x1={0} x2={innerW} y1={y(0)} y2={y(0)}
              stroke="var(--border)" strokeWidth={1} strokeDasharray="2,3"
            />
          )}
          {areaPath && <path d={areaPath} fill="var(--accent)" opacity={0.1} />}
          {path && <path d={path} fill="none" stroke="var(--accent)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />}
          {points.map((p, i) => (
            <circle
              key={i}
              cx={p[0]} cy={p[1]} r={hoverIdx === i ? 6 : 4}
              fill="var(--accent)" stroke="var(--bg)" strokeWidth={2}
            />
          ))}
          {hoverIdx != null && points[hoverIdx] && (
            <line
              x1={points[hoverIdx][0]} x2={points[hoverIdx][0]} y1={0} y2={innerH}
              stroke="var(--muted)" strokeWidth={1} strokeDasharray="2,3"
            />
          )}
        </g>
      </svg>
    </div>
  );
}
