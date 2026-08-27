/**
 * Lesson Plans -- the material library (teacher-010).
 *
 * Every material behind every subject this teacher is assigned to, filterable
 * by subject. View opens the file inline; Save downloads it. Both go through
 * GET /teacher/materials/{id}/file, which refuses material from a subject the
 * teacher does not teach.
 *
 * Was a static shelf of "Mathematics" and "Sciences" plans with buttons that
 * did nothing.
 */
import { useEffect, useMemo, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  cached,
  getTeacherMaterials,
  materialFileUrl,
  type TeacherMaterial,
} from "@/lib/api";

const KIND_LABEL: Record<string, string> = {
  textbook: "Textbook",
  syllabus: "Syllabus",
  assignment: "Assignment",
  reference: "Reference",
  notes: "Notes",
};

export default function LessonPlansLibraryHighContrast() {
  const [items, setItems] = useState<TeacherMaterial[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState<string>("all");

  useEffect(() => {
    let alive = true;
    cached("teacher-materials", getTeacherMaterials)
      .then((r) => alive && (setItems(r), setError(null)))
      .catch(() => alive && setError("Could not load the material library."));
    return () => {
      alive = false;
    };
  }, []);

  // the filter chips are the real subjects, not "Mathematics"/"Sciences"
  const subjects = useMemo(() => {
    const seen = new Map<string, string>();
    for (const m of items ?? []) {
      if (m.course_code) seen.set(m.course_code, m.course_title ?? m.course_code);
    }
    return [...seen.entries()];
  }, [items]);

  const shown = (items ?? []).filter((m) => subject === "all" || m.course_code === subject);

  return (
    <TeacherChrome active="lesson-plans">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-orange">auto_stories</span>
            Course material
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">
            Lesson Plans
          </h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            Every book and document behind the subjects you teach — the same corpus your students'
            answers are cited from.
          </p>
        </div>
        <span className="font-label-sm text-label-sm text-ink-soft">
          {items ? `${items.length} item${items.length === 1 ? "" : "s"}` : "…"}
        </span>
      </header>

      {/* Subject filter: real course codes */}
      <div className="flex flex-wrap gap-3 relative z-10">
        <button
          onClick={() => setSubject("all")}
          className={`px-5 py-2.5 rounded-full font-label-md text-label-md transition-colors border ${
            subject === "all"
              ? "bg-ink text-on-primary border-ink"
              : "border-ink/25 text-ink hover:border-orange"
          }`}
        >
          All subjects
        </button>
        {subjects.map(([code, title]) => (
          <button
            key={code}
            onClick={() => setSubject(code)}
            title={title}
            className={`px-5 py-2.5 rounded-full font-label-md text-label-md transition-colors border ${
              subject === code
                ? "bg-ink text-on-primary border-ink"
                : "border-ink/25 text-ink hover:border-orange"
            }`}
          >
            {code}
          </button>
        ))}
      </div>

      {error && (
        <p role="alert" className="bg-error/15 text-ink px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        {items && shown.length === 0 && !error && (
          <p className="font-body-lg text-body-lg text-ink-soft">
            No material for this subject yet — an admin uploads it from the console.
          </p>
        )}

        {shown.map((m) => (
          <article
            key={m.id}
            className="bg-card p-8 rounded-2xl border border-outline-variant shadow-[0_6px_14px_-10px_rgba(43,41,38,0.24)] flex flex-col gap-4"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <span className="font-label-sm text-label-sm uppercase tracking-widest text-ink-faint">
                  {m.course_code} · {KIND_LABEL[m.kind] ?? m.kind}
                </span>
                <h3 className="font-title-md text-title-md text-ink mt-1">{m.title}</h3>
              </div>
              {m.ingest_status !== "complete" && (
                <span className="shrink-0 bg-peach font-label-sm text-label-sm px-2 py-1 rounded font-semibold uppercase text-ink">
                  {m.ingest_status}
                </span>
              )}
            </div>

            <p className="font-label-sm text-label-sm text-ink-soft">
              {m.page_count > 0 && `${m.page_count} pages · `}
              {m.chunk_count > 0
                ? `${m.chunk_count.toLocaleString()} passages indexed`
                : "not indexed yet"}
            </p>

            <div className="flex gap-2 mt-auto pt-2">
              {m.has_file ? (
                <>
                  <a
                    href={materialFileUrl(m.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-ink"
                  >
                    View
                  </a>
                  <a href={materialFileUrl(m.id, true)} className="btn-ghost">
                    Save
                  </a>
                </>
              ) : (
                <span
                  className="font-label-sm text-label-sm text-ink-faint"
                  title="The row exists but the file is not on disk."
                >
                  File unavailable
                </span>
              )}
            </div>
          </article>
        ))}
      </div>
    </TeacherChrome>
  );
}
