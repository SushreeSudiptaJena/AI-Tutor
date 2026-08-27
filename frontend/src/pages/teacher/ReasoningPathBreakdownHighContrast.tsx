/**
 * Converted from stitch_ascent_educator_dashboard/reasoning_path_breakdown_high_contrast/reasoning_path_breakdown_high_contrast.html
 * Wired live (frontend-004): GET /teacher/problems/{problem_type}/reasoning-paths
 * (teacher-002). The problem types on offer are the real ones from the
 * heatmap; each card shows a real answer a real student gave, with the
 * misconception's reasoning description -- never a name.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  cached,
  getHeatmap,
  getReasoningPaths,
  type Heatmap,
  type ReasoningPathItem,
} from "@/lib/api";

export default function ReasoningPathBreakdownHighContrast() {
  const [heat, setHeat] = useState<Heatmap | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [items, setItems] = useState<ReasoningPathItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    cached("heatmap-teacher", getHeatmap)
      .then((h) => {
        if (!alive) return;
        setHeat(h);
        setSelected((cur) => cur ?? h.items[0]?.problem_type ?? null);
      })
      .catch(() => alive && setError("Could not load the problem types."));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!selected) return;
    let alive = true;
    setItems(null);
    cached(`reasoning:${selected}`, () => getReasoningPaths(selected))
      .then((r) => alive && (setItems(r), setError(null)))
      .catch(() => alive && setError("Could not load the reasoning paths."));
    return () => {
      alive = false;
    };
  }, [selected]);

  const types = [...new Set((heat?.items ?? []).map((i) => i.problem_type))];

  return (
    <TeacherChrome active="reasoning-path-breakdown">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">route</span>
            Diagnostic Insight
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">
            Reasoning Path Breakdown
          </h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            Behind one kind of problem: the wrong mental models students confirmed as their own,
            each with a real answer a real student gave. Anonymous — what was thought, not who.
          </p>
        </div>
      </header>

      {/* Problem-type selector: real types from the heatmap */}
      <div className="flex flex-wrap gap-3 relative z-10">
        {types.length === 0 && !error && (
          <span className="font-body-md text-body-md text-ink-soft">
            No confirmed misconceptions yet — there is nothing to break down.
          </span>
        )}
        {types.map((t) => (
          <button
            key={t}
            onClick={() => setSelected(t)}
            className={`px-5 py-2.5 rounded-full font-label-md text-label-md transition-colors border ${
              t === selected
                ? "bg-secondary text-ink border-secondary"
                : "border-ink/25 text-ink hover:border-secondary"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {error && (
        <p role="alert" className="bg-error/20 text-ink px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        {items?.length === 0 && !error && (
          <p className="font-body-lg text-body-lg text-ink-soft">
            No confirmed reasoning paths for this problem type yet.
          </p>
        )}
        {(items ?? []).map((it) => (
          <article
            key={it.misconception_id}
            className="bg-surface-container-lowest text-ink p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] flex flex-col gap-4"
          >
            <div className="flex items-start justify-between gap-4">
              <h3 className="font-title-md text-title-md leading-snug">{it.label}</h3>
              <span className="shrink-0 bg-secondary-container font-label-sm text-label-sm px-2 py-1 rounded font-semibold">
                {it.confirmed_count} confirmed
              </span>
            </div>
            {it.example ? (
              <div className="bg-tertiary-fixed/40 rounded-xl p-5 flex flex-col gap-3">
                <div>
                  <span className="font-label-sm text-label-sm uppercase tracking-widest text-ink/60">
                    A real student answered
                  </span>
                  <p className="font-title-md text-title-md mt-1">“{it.example.given_answer}”</p>
                </div>
                <div>
                  <span className="font-label-sm text-label-sm uppercase tracking-widest text-ink/60">
                    The reasoning behind it
                  </span>
                  <p className="font-body-md text-body-md mt-1">{it.example.reasoning}</p>
                </div>
              </div>
            ) : (
              <p className="font-body-md text-body-md text-ink/70">
                No stored example answer for this path yet.
              </p>
            )}
          </article>
        ))}
      </div>
    </TeacherChrome>
  );
}
