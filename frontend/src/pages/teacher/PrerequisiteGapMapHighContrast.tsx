/**
 * Converted from stitch_ascent_educator_dashboard/prerequisite_gap_map_high_contrast/prerequisite_gap_map_high_contrast.html
 * Wired live (frontend-003): GET /teacher/gap-map — prerequisite concepts the
 * class is missing, ranked by students_missing, attributed to the course the
 * gap came from (that attribution is the whole point of the map).
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import { getGapMap, type GapMapItem } from "@/lib/api";

export default function PrerequisiteGapMapHighContrast() {
  const [items, setItems] = useState<GapMapItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    getGapMap()
      .then((r) => alive && (setItems(r), setError(null)))
      .catch(() => alive && setError("Could not load the gap map."));
    return () => {
      alive = false;
    };
  }, []);

  const max = Math.max(...(items ?? []).map((i) => i.students_missing), 1);

  return (
    <TeacherChrome active="gap-map">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">map</span>
            Prerequisite Coverage
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">
            Prerequisite Gap Map
          </h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            What this class is missing from earlier courses, ranked by how many students carry the
            gap. Each row names the course it should have been learned in.
          </p>
        </div>
        <div className="flex flex-col text-right">
          <span className="font-title-md text-title-md text-ink">
            {items ? `${items.length} concepts` : "…"}
          </span>
          <span className="font-label-sm text-label-sm text-ink">open gaps across the class</span>
        </div>
      </header>

      {error && (
        <p role="alert" className="bg-error/20 text-ink px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        {items?.length === 0 && !error && (
          <p className="font-body-lg text-body-lg text-ink-soft">
            No open prerequisite gaps — the class diagnostic came back clean.
          </p>
        )}
        {(items ?? []).map((g) => (
          <article
            key={g.concept}
            className="bg-tertiary-fixed text-ink p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] flex flex-col gap-4"
          >
            <div className="flex items-start justify-between gap-4">
              <h3 className="font-title-md text-title-md leading-snug">{g.concept}</h3>
              <span className="shrink-0 bg-secondary-container font-label-sm text-label-sm px-2 py-1 rounded font-semibold">
                {Math.round(g.share * 100)}% of class
              </span>
            </div>
            <p className="font-body-md text-body-md text-ink/80 flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">history_edu</span>
              From <strong>{g.prerequisite_course}</strong>
            </p>
            <div className="mt-2">
              <div className="flex justify-between font-label-sm text-label-sm mb-1">
                <span className="font-semibold uppercase">Students missing</span>
                <span>{g.students_missing}</span>
              </div>
              <div className="w-full bg-ink/10 h-3 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full rounded-full"
                  style={{ width: `${(g.students_missing / max) * 100}%` }}
                ></div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </TeacherChrome>
  );
}
