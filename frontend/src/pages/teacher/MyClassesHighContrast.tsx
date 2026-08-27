/**
 * My Classes -- the subjects this teacher actually teaches.
 *
 * Was a static roster of 9A / 10C / Mathematics sections with a "Create New
 * Class" box. A teacher does not create classes here: an admin assigns them
 * to subjects (admin-009), so the box promised something the API refuses.
 * This lists the real assignments, with the cohorts each one serves.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  cached,
  getTeacherSubjects,
  invalidateCache,
  setTeacherActiveSubject,
  type TeacherSubject,
} from "@/lib/api";

export default function MyClassesHighContrast() {
  const [subjects, setSubjects] = useState<TeacherSubject[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    cached("teacher-subjects", getTeacherSubjects)
      .then((r) => alive && (setSubjects(r), setError(null)))
      .catch(() => alive && setError("Could not load your subjects."));
    return () => {
      alive = false;
    };
  }, []);

  async function open(courseId: number) {
    setBusy(true);
    try {
      await setTeacherActiveSubject(courseId);
      invalidateCache("teacher-subjects");
      window.location.reload();
    } catch {
      setBusy(false);
    }
  }

  return (
    <TeacherChrome active="my-classes">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-orange">school</span>
            Your teaching load
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">My Classes</h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            The subjects your department admin has assigned you, and the cohorts taking each one.
          </p>
        </div>
      </header>

      {error && (
        <p role="alert" className="bg-error/15 text-ink px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        {subjects?.length === 0 && !error && (
          <p className="font-body-lg text-body-lg text-ink-soft">
            No subjects assigned yet — your admin assigns them from the console.
          </p>
        )}

        {(subjects ?? []).map((s) => (
          <article
            key={s.id}
            className={`bg-card p-8 rounded-2xl border shadow-[0_6px_14px_-10px_rgba(43,41,38,0.24)] flex flex-col gap-4 ${
              s.is_current ? "border-orange" : "border-outline-variant"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <span className="font-label-sm text-label-sm uppercase tracking-widest text-ink-faint">
                  {s.code}
                  {s.semester !== null && ` · semester ${s.semester}`}
                </span>
                <h3 className="font-title-md text-title-md text-ink mt-1">{s.title}</h3>
              </div>
              {s.is_current && (
                <span className="shrink-0 bg-peach-2 text-ink font-label-sm text-label-sm px-2 py-1 rounded font-semibold uppercase">
                  Showing
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {s.batches.length === 0 ? (
                <span className="font-label-sm text-label-sm text-ink-faint italic">
                  No cohort takes this yet
                </span>
              ) : (
                s.batches.map((b) => (
                  <span
                    key={b.id}
                    className="px-3 py-1 rounded-full bg-paper-2 border border-outline-variant font-label-sm text-label-sm text-ink"
                  >
                    {b.major.toUpperCase()} · {b.department} · {b.start_year}–{b.end_year}
                  </span>
                ))
              )}
            </div>

            <div className="mt-auto pt-2">
              {s.is_current ? (
                <span className="font-label-sm text-label-sm text-ink-soft">
                  This is the subject the console is showing.
                </span>
              ) : (
                <button
                  onClick={() => open(s.id)}
                  disabled={busy}
                  className="btn-ink disabled:opacity-50"
                >
                  Show this class
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </TeacherChrome>
  );
}
