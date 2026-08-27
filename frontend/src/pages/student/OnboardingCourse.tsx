import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, GraduationCap } from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
  ApiError,
  enroll,
  getEnrollableBatches,
  getMySubjects,
  MAJOR_YEARS,
  type BatchDto,
  type MySubject,
} from "@/lib/api";

/**
 * student-010. Enrolment: pick the cohort you were admitted to, then the
 * subject to start with.
 *
 * This page used to assume the student already had a course and simply
 * described it -- which 400'd for anyone who had just signed up, since a new
 * account has no course_id at all. Now it is where the account actually gets
 * one.
 */

const MAJOR_LABELS: Record<string, string> = {
  btech: "BTech",
  bca: "BCA",
  mtech: "MTech",
  mca: "MCA",
};

function label(b: BatchDto): string {
  return `${MAJOR_LABELS[b.major] ?? b.major.toUpperCase()} · ${b.department.name}`;
}

export default function OnboardingCourse() {
  const navigate = useNavigate();
  const [batches, setBatches] = useState<BatchDto[] | null>(null);
  const [picked, setPicked] = useState<BatchDto | null>(null);
  const [subjects, setSubjects] = useState<MySubject[] | null>(null);
  const [chosen, setChosen] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Already enrolled (the seeded students are) -- show their cohort rather
    // than making them pick again.
    getMySubjects()
      .then((r) => {
        if (r.batch) {
          setPicked(r.batch);
          setSubjects(r.items);
          setChosen(r.items.find((s) => s.is_current)?.id ?? null);
        }
      })
      .catch(() => {});
    getEnrollableBatches()
      .then(setBatches)
      .catch((caught) =>
        setError(caught instanceof ApiError ? caught.message : "Couldn't load the batches."),
      );
  }, []);

  async function choose(b: BatchDto) {
    setError("");
    if (b.course_count === 0) {
      setError("That batch has no subjects yet — ask your admin to add them.");
      return;
    }
    setBusy(true);
    try {
      await enroll(b.id);
      const r = await getMySubjects();
      setPicked(r.batch);
      setSubjects(r.items);
      setChosen(r.items.find((s) => s.is_current)?.id ?? null);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Couldn't enrol you just now.");
    } finally {
      setBusy(false);
    }
  }

  async function start() {
    if (!picked || chosen === null) return;
    setBusy(true);
    setError("");
    try {
      await enroll(picked.id, chosen);
      navigate("/onboarding/diagnostic");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Couldn't set your subject.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-cream px-md py-xl text-on-surface sm:px-xl">
      <div className="mx-auto max-w-3xl">
        <p className="text-label-md font-bold tracking-[0.3em] text-forest-green">JOURNEY / 01</p>

        <div className="mt-xl grid gap-xl md:grid-cols-[0.8fr_1.2fr] md:items-start">
          <div>
            <BookOpen className="h-10 w-10 text-mustard" />
            <h1 className="mt-md font-serif text-5xl leading-tight">
              {picked ? "Pick your first subject." : "Find your batch."}
            </h1>
            <p className="mt-md text-body-lg text-on-surface-variant">
              {picked
                ? "You can switch subjects any time — your gaps and practice stay with each one."
                : "Your batch decides which subjects you'll see. Everyone is welcome in this build."}
            </p>
            {picked && (
              <p className="mt-md inline-flex items-center gap-xs rounded-full bg-sage-light px-sm py-xs text-label-sm">
                <GraduationCap className="h-4 w-4" />
                {label(picked)} · {picked.start_year}–{picked.end_year}
              </p>
            )}
          </div>

          <div className="border border-outline-variant bg-card p-lg shadow-sm">
            {error && (
              <p className="mb-md text-body-sm text-error" role="alert">
                {error}
              </p>
            )}

            {!picked ? (
              batches === null ? (
                <p className="text-on-surface-variant">Loading batches…</p>
              ) : batches.length === 0 ? (
                <p className="text-on-surface-variant">
                  No batches exist yet. Your college admin creates these — check back once they
                  have.
                </p>
              ) : (
                <ul className="flex flex-col gap-sm">
                  {batches.map((b) => (
                    <li key={b.id}>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => choose(b)}
                        className="w-full border border-outline-variant px-md py-sm text-left transition-colors hover:border-forest-green disabled:opacity-50"
                      >
                        <span className="block text-body-md font-bold">{label(b)}</span>
                        <span className="block text-label-sm text-on-surface-variant">
                          {b.start_year}–{b.end_year} · {MAJOR_YEARS[b.major] ?? "?"} years ·{" "}
                          {b.course_count} subject{b.course_count === 1 ? "" : "s"}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )
            ) : (
              <>
                <ul className="flex flex-col gap-xs">
                  {(subjects ?? []).map((s) => (
                    <li key={s.id}>
                      <button
                        type="button"
                        onClick={() => setChosen(s.id)}
                        className={`w-full border px-md py-sm text-left transition-colors ${
                          chosen === s.id
                            ? "border-forest-green bg-sage-light"
                            : "border-outline-variant hover:border-forest-green"
                        }`}
                      >
                        <span className="text-label-md font-bold text-forest-green">{s.code}</span>
                        <span className="ml-xs text-body-md">{s.title}</span>
                        {s.semester !== null && (
                          <span className="ml-xs text-label-sm text-on-surface-variant">
                            semester {s.semester}
                          </span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() => {
                    setPicked(null);
                    setSubjects(null);
                    setChosen(null);
                  }}
                  className="mt-md text-label-sm text-on-surface-variant underline"
                >
                  Choose a different batch
                </button>
              </>
            )}
          </div>
        </div>

        <button
          className="mt-xl flex items-center gap-sm bg-forest-green px-lg py-md font-bold text-white hover:bg-forest-light disabled:opacity-50"
          onClick={start}
          disabled={busy || !picked || chosen === null}
          type="button"
        >
          {busy ? "Setting up…" : "Continue"} <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </main>
  );
}
