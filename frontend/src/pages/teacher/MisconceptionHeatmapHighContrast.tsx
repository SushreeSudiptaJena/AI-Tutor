/**
 * Converted from stitch_ascent_educator_dashboard/misconception_heatmap_high_contrast/misconception_heatmap_high_contrast.html
 * Wired live (frontend-003): GET /teacher/misconceptions/heatmap, polled
 * every 5s per the contract -- the number moves when a student confirms a
 * diagnosis on another laptop. Share bands drive the impact colouring.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import { getHeatmap, type Heatmap } from "@/lib/api";

const POLL_MS = 5000;

function band(share: number): { label: string; chip: string; bar: string } {
  if (share >= 0.3)
    return { label: "CRITICAL", chip: "bg-error-container", bar: "bg-error" };
  if (share >= 0.15)
    return { label: "HIGH", chip: "bg-secondary-container", bar: "bg-secondary" };
  if (share >= 0.05)
    return { label: "MODERATE", chip: "bg-surface-variant", bar: "bg-outline-variant" };
  return { label: "LOW", chip: "bg-surface-variant", bar: "bg-outline-variant" };
}

function since(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  return `${hrs}h ago`;
}

export default function MisconceptionHeatmapHighContrast() {
  const [data, setData] = useState<Heatmap | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      getHeatmap()
        .then((d) => alive && (setData(d), setError(null)))
        .catch(() => alive && setError("Could not load the heatmap."));
    load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  const items = data?.items ?? [];
  const top = items[0];
  const critical = items.filter((i) => i.share >= 0.3).length;
  const moderate = items.filter((i) => i.share >= 0.15 && i.share < 0.3).length;
  const low = items.filter((i) => i.share < 0.15).length;
  const max = Math.max(...items.map((i) => i.share), 0.01);

  return (
    <TeacherChrome active="misconception-heatmap">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-[#FFFFFF]/20 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-[#FFFFFF] mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">thermostat</span>
            Cognitive Analytics
          </span>
          <h1 className="font-display-lg text-display-lg text-[#FFFFFF] m-0 leading-tight">
            Misconception Heatmap
          </h1>
          <p className="font-body-lg text-body-lg text-[#FFFFFF] mt-4 max-w-[36rem]">
            Only diagnoses a student CONFIRMED as their own reasoning are counted. Updates live as the class practises.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex flex-col text-right">
            <span className="font-title-md text-title-md text-[#FFFFFF]">
              Class size: {data?.class_size ?? "…"}
            </span>
            <span className="font-label-sm text-label-sm text-[#FFFFFF]">
              Last updated: {data ? since(data.updated_at) : "…"}
            </span>
          </div>
        </div>
      </header>

      {error && (
        <p role="alert" className="bg-error/20 text-[#FFFFFF] px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10">
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-tertiary-fixed text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
            <div className="absolute -right-12 -top-12 w-40 h-40 bg-secondary/10 rounded-full blur-2xl group-hover:bg-secondary/20 transition-colors"></div>
            <h3 className="font-title-md text-title-md mb-6 pb-4 border-b border-tertiary-fixed-dim/50 flex justify-between items-center text-[#1A1A1A]">
              Primary Intervention Target
              <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
                warning
              </span>
            </h3>
            {top ? (
              <div className="flex flex-col gap-2">
                <span className="font-display-lg text-display-lg text-[#1A1A1A]">
                  {Math.round(top.share * 100)}%
                </span>
                <span className="font-body-md text-body-md text-[#1A1A1A]">
                  of the class consistently demonstrated flawed reasoning in:
                </span>
                <strong className="font-title-md text-title-md mt-2 text-[#1A1A1A]">{top.label}</strong>
              </div>
            ) : (
              <p className="font-body-md text-body-md text-[#1A1A1A]">
                No confirmed misconceptions yet — the map fills as students practise and confirm what
                the diagnostic surfaced.
              </p>
            )}
          </div>

          <div className="bg-surface-container-lowest text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)]">
            <h3 className="font-title-md text-title-md mb-6 pb-4 border-b border-[#1A1A1A]/20 text-[#1A1A1A]">
              Overall Impact Distribution
            </h3>
            <div className="flex flex-col gap-5">
              {[
                ["Critical Impact (Requires Immediate Reteach)", critical, "bg-error"],
                ["Moderate Impact (Address in Review)", moderate, "bg-secondary"],
                ["Low Impact (Monitor)", low, "bg-outline-variant"],
              ].map(([label, count, color]) => (
                <div key={label as string} className="flex flex-col gap-1">
                  <div className="flex justify-between font-label-sm text-label-sm">
                    <span className="text-[#1A1A1A] font-semibold">{label as string}</span>
                    <span className="text-[#1A1A1A]">{count as number}</span>
                  </div>
                  <div className="w-full bg-[#1A1A1A]/10 h-2 rounded-full overflow-hidden">
                    <div
                      className={`${color as string} h-full rounded-full transition-all`}
                      style={{ width: `${Math.min(100, ((count as number) / Math.max(items.length, 1)) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Was a decorative stock image on a googleusercontent URL that has
              since expired -- a gradient keeps the tile with zero network. */}
          <div className="rounded-2xl overflow-hidden h-48 relative shadow-md">
            <div className="absolute inset-0 bg-gradient-to-br from-tertiary-fixed via-surface-tint/40 to-inverse-surface"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="material-symbols-outlined text-[#1A1A1A]/40 text-[64px]">insights</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-8 flex flex-col">
          <div className="bg-tertiary-fixed text-[#1A1A1A] rounded-2xl shadow-[0_8px_60px_rgba(0,0,0,0.08)] overflow-hidden flex flex-col h-full">
            <div className="px-8 py-6 border-b border-tertiary-fixed-dim bg-tertiary-fixed-dim/20 flex items-center justify-between">
              <h2 className="font-headline-lg text-headline-lg text-[#1A1A1A]">Identified Mental Models</h2>
              <div className="flex items-center gap-3 bg-surface-container-lowest/50 px-4 py-2 rounded-full border border-outline-variant/30">
                <span className="material-symbols-outlined text-outline text-[18px]">filter_list</span>
                <span className="font-label-sm text-label-sm text-[#1A1A1A]">Sort by: Confirmed students (desc)</span>
              </div>
            </div>

            <div className="flex flex-col divide-y divide-tertiary-fixed-dim/40 overflow-y-auto">
              {items.length === 0 && !error && (
                <p className="px-8 py-10 font-body-md text-body-md text-[#1A1A1A]/70">
                  Nothing confirmed yet.
                </p>
              )}
              {items.map((it) => {
                const b = band(it.share);
                return (
                  <div
                    key={it.misconception_id}
                    className="px-8 py-6 hover:bg-tertiary-fixed-dim/10 transition-colors group relative flex flex-col md:flex-row gap-6 items-start md:items-center"
                  >
                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${b.bar} opacity-100 group-hover:w-2 transition-all`}></div>
                    <div className="flex-1 flex flex-col gap-2 min-w-0 pr-4">
                      <div className="flex items-center gap-3">
                        <span className={`${b.chip} text-[#1A1A1A] font-label-sm text-label-sm px-2 py-1 rounded font-semibold`}>
                          {b.label}
                        </span>
                        <h4 className="font-title-md text-title-md truncate text-[#1A1A1A]">{it.label}</h4>
                      </div>
                      <p className="font-body-md text-body-md text-[#1A1A1A] line-clamp-2">
                        Problem type <code className="font-label-sm">{it.problem_type}</code> — {it.confirmed_count} student
                        {it.confirmed_count === 1 ? "" : "s"} confirmed this exact reasoning.
                      </p>
                    </div>
                    <div className="flex items-center gap-8 shrink-0">
                      <div className="flex flex-col items-end">
                        <span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Frequency</span>
                        <span className="font-headline-lg text-headline-lg text-[#1A1A1A]">
                          {Math.round(it.share * 100)}%
                        </span>
                      </div>
                      <div className="w-24 h-2 bg-[#1A1A1A]/10 rounded-full overflow-hidden hidden md:block">
                        <div className={`${b.bar} h-full rounded-full`} style={{ width: `${(it.share / max) * 100}%` }}></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="px-8 py-4 border-t border-tertiary-fixed-dim bg-tertiary-fixed-dim/10 flex justify-between items-center mt-auto">
              <span className="font-label-sm text-label-sm text-[#1A1A1A]/70">
                Polling every {POLL_MS / 1000}s — no refresh needed
              </span>
              <span className="font-label-sm text-label-sm text-[#1A1A1A]/70">
                {items.length} shown
              </span>
            </div>
          </div>
        </div>
      </div>
    </TeacherChrome>
  );
}
