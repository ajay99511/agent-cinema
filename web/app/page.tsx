"use client";

import { useState } from "react";

type AskResponse = {
  session_id?: string;
  answer?: string;
  sql_shown?: string[];
  data?: unknown[];
  error?: string;
  detail?: string;
};

const EXAMPLES = [
  "What is the average conflict of the scenes?",
  "Which scene has the lowest valence?",
  "How many scenes are in each act?",
];

export default function Home() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>();

  async function ask(question: string) {
    if (!question.trim() || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message: question, session_id: sessionId }),
      });
      const json: AskResponse = await res.json();
      setResult(json);
      if (json.session_id) setSessionId(json.session_id);
    } catch (err) {
      setResult({ error: "request failed", detail: String(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="wrap">
      <h1>Screenplay Structural Map</h1>
      <p className="subtitle">
        Ask about the screenplay corpus. Every number is produced by a live ClickHouse query —
        expand “SQL” to see it.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(message);
        }}
      >
        <input
          type="text"
          value={message}
          placeholder="Ask a question about the screenplay…"
          onChange={(e) => setMessage(e.target.value)}
          aria-label="Question"
        />
        <button type="submit" disabled={loading || !message.trim()}>
          {loading ? "Asking…" : "Ask"}
        </button>
      </form>

      <p className="hint">
        Try:{" "}
        {EXAMPLES.map((ex, i) => (
          <span key={ex}>
            {i > 0 && " · "}
            <button
              type="button"
              onClick={() => {
                setMessage(ex);
                ask(ex);
              }}
            >
              {ex}
            </button>
          </span>
        ))}
      </p>

      {result && (
        <div className="card">
          <h2>Answer</h2>
          {result.error ? (
            <p className="answer error">
              {result.error}
              {result.detail ? ` — ${result.detail}` : ""}
            </p>
          ) : (
            <p className="answer">{result.answer || "(no answer returned)"}</p>
          )}

          {result.sql_shown && result.sql_shown.length > 0 && (
            <details open>
              <summary>SQL run against ClickHouse ({result.sql_shown.length})</summary>
              {result.sql_shown.map((sql, i) => (
                <pre key={i}>{sql}</pre>
              ))}
            </details>
          )}

          {result.data && result.data.length > 0 && (
            <details>
              <summary>Raw data</summary>
              <pre>{JSON.stringify(result.data, null, 2)}</pre>
            </details>
          )}
        </div>
      )}
    </main>
  );
}
