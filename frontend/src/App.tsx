import { useEffect, useState } from "react";
import { getHealth, getLanguages } from "@/lib/api";

/**
 * infra-002 baseline screen: proves the frontend can reach the backend.
 * Replaced by the real router once auth-001 lands.
 */
export default function App() {
  const [health, setHealth] = useState<string>("checking…");
  const [langs, setLangs] = useState<string[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    getHealth()
      .then((h) => setHealth(`${h.status} · db ${h.db}`))
      .catch((e) => setError(e.message));
    getLanguages()
      .then((l) => setLangs(l.items.map((i) => i.label)))
      .catch(() => {});
  }, []);

  return (
    <main className="mx-auto max-w-xl p-8 font-sans">
      <h1 className="text-2xl font-semibold">AI Tutor</h1>
      <p className="mt-1 text-sm opacity-70">
        Curriculum-aligned adaptive tutor — baseline check
      </p>

      <dl className="mt-6 space-y-2 text-sm">
        <div className="flex gap-2">
          <dt className="w-28 opacity-60">API base</dt>
          <dd className="font-mono">{import.meta.env.VITE_API_BASE ?? "http://localhost:8000"}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-28 opacity-60">Backend</dt>
          <dd className="font-mono">{error ? `unreachable — ${error}` : health}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-28 opacity-60">Languages</dt>
          <dd>{langs.length ? langs.join(", ") : "—"}</dd>
        </div>
      </dl>

      {error && (
        <p className="mt-6 rounded border border-amber-400 bg-amber-50 p-3 text-sm">
          Can’t reach the backend. Check <code>VITE_API_BASE</code> in{" "}
          <code>frontend/.env.local</code> — the tunnel URL changes on every restart.
        </p>
      )}
    </main>
  );
}
