/**
 * Converted from stitch_ascent_educator_dashboard/dashboard_overview_high_contrast/dashboard_overview_high_contrast.html
 * Wired live (frontend-004): the overview's numbers are now real aggregates
 * (heatmap, gap map, uncertainty flags). One deliberate substitution: the
 * mockup's "Avg. Mastery" card is GONE — an aggregate mastery score does not
 * exist anywhere in this system by design (see the contract's stance), and a
 * dashboard that invents one would undercut the whole build. Its slot holds
 * the open-gap count instead.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  cached,
  getGapMap,
  getHeatmap,
  getUncertaintyFlags,
  type GapMapItem,
  type Heatmap,
  type UncertaintyFlagDto,
} from "@/lib/api";

export default function DashboardOverviewHighContrast() {
  const [heat, setHeat] = useState<Heatmap | null>(null);
  const [gaps, setGaps] = useState<GapMapItem[] | null>(null);
  const [flags, setFlags] = useState<UncertaintyFlagDto[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    Promise.all([
      cached("heatmap-teacher", getHeatmap),
      cached("gap-map", getGapMap),
      cached("flags-open", () => getUncertaintyFlags("open")),
    ])
      .then(([h, g, f]) => {
        if (!alive) return;
        setHeat(h);
        setGaps(g);
        setFlags(f);
        setError(null);
      })
      .catch(() => alive && setError("Could not load the overview."));
    return () => {
      alive = false;
    };
  }, []);

  const top = heat?.items?.[0];
  const tiles = [
    { icon: "groups", label: "Class size", value: heat ? String(heat.class_size) : "…" },
    {
      icon: "warning",
      label: "Open uncertainty flags",
      value: flags ? String(flags.length) : "…",
    },
    {
      icon: "thermostat",
      label: "Top misconception share",
      value: top ? `${Math.round(top.share * 100)}%` : "—",
    },
    {
      icon: "map",
      label: "Open prerequisite gaps",
      value: gaps ? String(gaps.length) : "…",
    },
  ];

  return (
    <TeacherChrome active="dashboard">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-[#FFFFFF]/20 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-[#FFFFFF] mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">dashboard</span>
            Today
          </span>
          <h1 className="font-display-lg text-display-lg text-[#FFFFFF] m-0 leading-tight">
            Class Overview
          </h1>
          <p className="font-body-lg text-body-lg text-[#FFFFFF] mt-4 max-w-xl">
            Live aggregates from your class's own practice — confirmed misconceptions, prerequisite
            gaps, and the questions the tutor could not ground in the material.
          </p>
        </div>
      </header>

      {error && (
        <p role="alert" className="bg-error/20 text-[#FFFFFF] px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
        {tiles.map((t) => (
          <div
            key={t.label}
            className="bg-tertiary-fixed text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] flex flex-col gap-3"
          >
            <span className="material-symbols-outlined text-secondary text-[28px]">{t.icon}</span>
            <span className="font-display-lg text-display-lg">{t.value}</span>
            <span className="font-label-sm text-label-sm uppercase tracking-widest text-[#1A1A1A]/60">
              {t.label}
            </span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        <section className="bg-surface-container-lowest text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)]">
          <h2 className="font-title-md text-title-md mb-6 pb-4 border-b border-[#1A1A1A]/10">
            Top Learning Gaps
          </h2>
          <div className="flex flex-col gap-4">
            {(gaps ?? []).slice(0, 5).map((g) => (
              <div key={g.concept} className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-title-md text-title-md truncate">{g.concept}</p>
                  <p className="font-label-sm text-label-sm text-[#1A1A1A]/60">
                    From {g.prerequisite_course}
                  </p>
                </div>
                <span className="shrink-0 font-headline-lg text-headline-lg">
                  {g.students_missing}
                </span>
              </div>
            ))}
            {gaps?.length === 0 && (
              <p className="font-body-md text-body-md text-[#1A1A1A]/70">
                No open gaps — the class diagnostic came back clean.
              </p>
            )}
          </div>
        </section>

        <section className="bg-surface-container-lowest text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)]">
          <h2 className="font-title-md text-title-md mb-6 pb-4 border-b border-[#1A1A1A]/10">
            Latest Uncertainty Flags
          </h2>
          <div className="flex flex-col gap-4">
            {(flags ?? []).slice(0, 4).map((f) => (
              <div key={f.id} className="flex items-start justify-between gap-4">
                <p className="font-body-md text-body-md line-clamp-2">{f.question}</p>
                <span className="shrink-0 bg-error-container font-label-sm text-label-sm px-2 py-1 rounded font-semibold">
                  {f.alignment_percent}%
                </span>
              </div>
            ))}
            {flags?.length === 0 && (
              <p className="font-body-md text-body-md text-[#1A1A1A]/70">
                No open flags — everything the class asked is grounded in the material.
              </p>
            )}
          </div>
        </section>
      </div>
    </TeacherChrome>
  );
}
