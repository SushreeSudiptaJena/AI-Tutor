/**
 * Converted from stitch_ascent_educator_dashboard/before_after_tracking_high_contrast/before_after_tracking_high_contrast.html
 * Wired live (frontend-004): GET /teacher/misconceptions/{id}/before-after
 * (teacher-005). The one panel that can report the intervention did NOT
 * work. The backend's null-vs-zero distinction is rendered, not smoothed
 * over: `after` null means no reteach yet; `delta_share` null means not
 * enough has happened since the reteach to measure anything.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  cached,
  getBeforeAfter,
  getHeatmap,
  type BeforeAfter,
  type BeforeAfterWindow,
  type Heatmap,
} from "@/lib/api";

function WindowCard({
  title,
  w,
  bgClass,
}: {
  title: string;
  w: BeforeAfterWindow | null;
  bgClass: string; // full literal class -- Tailwind only generates what it can scan
}) {
  return (
    <div className={`${bgClass} text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] flex flex-col gap-3`}>
      <span className="font-label-sm text-label-sm uppercase tracking-widest text-[#1A1A1A]/60">
        {title}
      </span>
      {w ? (
        <>
          <span className="font-display-lg text-display-lg">
            {Math.round(w.share * 100)}%
          </span>
          <span className="font-body-md text-body-md">
            {w.confirmed_count} student{w.confirmed_count === 1 ? "" : "s"} confirmed this reasoning
          </span>
          <span className="font-label-sm text-label-sm text-[#1A1A1A]/60">
            {w.window}
            {w.attempts_in_window !== undefined && ` · ${w.attempts_in_window} attempts in window`}
          </span>
        </>
      ) : (
        <span className="font-body-md text-body-md text-[#1A1A1A]/70">
          No reteach approved for this misconception yet — nothing to compare against.
        </span>
      )}
    </div>
  );
}

export default function BeforeAfterTrackingHighContrast() {
  const [heat, setHeat] = useState<Heatmap | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [data, setData] = useState<BeforeAfter | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    cached("heatmap-teacher", getHeatmap)
      .then((h) => {
        if (!alive) return;
        setHeat(h);
        setSelected((cur) => cur ?? h.items[0]?.misconception_id ?? null);
      })
      .catch(() => alive && setError("Could not load the misconceptions."));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (selected === null) return;
    let alive = true;
    setData(null);
    getBeforeAfter(selected)
      .then((d) => alive && (setData(d), setError(null)))
      .catch(() => alive && setError("Could not load the before/after data."));
    return () => {
      alive = false;
    };
  }, [selected]);

  const delta = data?.delta_share;
  const deltaText =
    delta === null || delta === undefined
      ? null
      : `${delta > 0 ? "+" : ""}${Math.round(delta * 100)}pp`;
  const improved = delta !== null && delta < 0;

  return (
    <TeacherChrome active="tracking">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-[#FFFFFF]/20 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-[#FFFFFF] mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">analytics</span>
            Intervention Impact
          </span>
          <h1 className="font-display-lg text-display-lg text-[#FFFFFF] m-0 leading-tight">
            Before / After Tracking
          </h1>
          <p className="font-body-lg text-body-lg text-[#FFFFFF] mt-4 max-w-xl">
            Confirmed occurrences of a misconception either side of its reteach. The delta is shown
            whatever its sign — including "it made no difference".
          </p>
        </div>
      </header>

      {/* Misconception selector: real ones from the heatmap */}
      <div className="flex flex-wrap gap-3 relative z-10">
        {(heat?.items ?? []).length === 0 && !error && (
          <span className="font-body-md text-body-md text-[#FFFFFF]/70">
            No confirmed misconceptions yet — nothing to track.
          </span>
        )}
        {(heat?.items ?? []).map((m) => (
          <button
            key={m.misconception_id}
            onClick={() => setSelected(m.misconception_id)}
            className={`px-5 py-2.5 rounded-full font-label-md text-label-md transition-colors border max-w-[24rem] truncate ${
              m.misconception_id === selected
                ? "bg-secondary text-[#1A1A1A] border-secondary"
                : "border-[#FFFFFF]/30 text-[#FFFFFF] hover:border-secondary"
            }`}
            title={m.label}
          >
            {m.label}
          </button>
        ))}
      </div>

      {error && (
        <p role="alert" className="bg-error/20 text-[#FFFFFF] px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10 items-stretch">
            <WindowCard title="Before the reteach" w={data.before} bgClass="bg-tertiary-fixed" />
            <div className="flex flex-col items-center justify-center gap-2 p-4">
              <span className="material-symbols-outlined text-[64px] text-secondary">arrow_range</span>
              {deltaText ? (
                <span
                  className={`font-headline-lg text-headline-lg px-4 py-1 rounded-full ${
                    improved ? "bg-secondary text-[#1A1A1A]" : "bg-error-container text-[#1A1A1A]"
                  }`}
                >
                  {deltaText}
                </span>
              ) : (
                <span className="font-label-md text-label-md text-[#FFFFFF]/70 text-center">
                  Not measured yet
                </span>
              )}
              {data.reteach_at && (
                <span className="font-label-sm text-label-sm text-[#FFFFFF]/50">
                  Reteach approved {new Date(data.reteach_at).toLocaleDateString()}
                </span>
              )}
            </div>
            <WindowCard title="After the reteach" w={data.after} bgClass="bg-surface-container-lowest" />
          </div>

          {delta === null && data.after && (
            <p className="border border-secondary/40 bg-secondary/10 text-[#FFFFFF] px-6 py-4 rounded-xl relative z-10">
              {data.note ??
                "Nobody has been asked since the reteach — zero evidence is not the same as zero occurrences. The delta appears once a student practises this problem type again."}
            </p>
          )}
          {delta !== null && improved && (
            <p className="border border-secondary/40 bg-secondary/10 text-[#FFFFFF] px-6 py-4 rounded-xl relative z-10">
              Fewer students confirm this reasoning after the reteach — {data.after?.attempts_in_window} attempts
              in the window make this a real measurement.
            </p>
          )}
          {delta !== null && !improved && (
            <p className="border border-error/40 bg-error/10 text-[#FFFFFF] px-6 py-4 rounded-xl relative z-10">
              This misconception is not shrinking — {delta === 0 ? "the reteach made no measurable difference yet" : "it is growing"}. Worth a different approach.
            </p>
          )}
        </>
      )}
    </TeacherChrome>
  );
}
