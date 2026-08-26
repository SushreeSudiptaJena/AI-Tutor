/**
 * admin-009 -- the batch-centric admin surface.
 *
 * Dashboard (default view): live institution metrics + the "Add batch"
 * 3-step modal. Batches: the cohort list with curriculum actions. The
 * Teachers dialog hangs off each subject card in the main dashboard file.
 *
 * Majors are fixed by the contract (btech 4, bca 3, mtech 2, mca 2); the
 * end year is previewed here but computed by the server regardless.
 */

import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  addBatchCourse,
  addCourseTeacher,
  createBatch,
  getBatchCourses,
  getBatches,
  getCourseTeachers,
  getOverview,
  listDepartments,
  MAJOR_YEARS,
  removeBatchCourse,
  removeCourseTeacher,
  reuseBatchCurriculum,
  uploadBatchCurriculum,
  listCourses,
  type AssignedTeacher,
  type BatchCourse,
  type BatchDto,
  type Course,
  type OverviewDto,
} from "@/lib/api";

function Icon({ name, className = "" }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>;
}

/** The admin shell's tab keys, defined here so both files share one type
 *  without a circular import (AdminDashboard imports this file). */
export type AdminTabKey =
  | "dashboard"
  | "batches"
  | "upload"
  | "structure"
  | "audit"
  | "profile"
  | "settings";

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Try again.";
}

export const MAJOR_LABELS: Record<string, string> = {
  btech: "BTech",
  bca: "BCA",
  mtech: "MTech",
  mca: "MCA",
};

const THIS_YEAR = new Date().getFullYear();

/* ------------------------------------------------------------------------ */
/* Dashboard view                                                            */
/* ------------------------------------------------------------------------ */

export function DashboardView({ goToTab }: { goToTab: (t: AdminTabKey) => void }) {
  const [ov, setOv] = useState<OverviewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [batches, setBatches] = useState<BatchDto[]>([]);

  const load = () =>
    Promise.all([getOverview(), getBatches()])
      .then(([o, b]) => {
        setOv(o);
        setBatches(b);
        setError(null);
      })
      .catch((err) => setError(errorText(err)));

  useEffect(() => {
    load();
  }, []);

  const tiles = [
    { icon: "groups", label: "Batches", value: ov?.batches ?? "…", hint: `${ov?.departments ?? "…"} departments` },
    {
      icon: "school",
      label: "Subjects",
      value: ov?.courses ?? "…",
      hint: `${ov?.materials ?? "…"} materials · ${ov?.courses_without_batch ?? "…"} in no batch`,
    },
    {
      icon: "person_book",
      label: "Teachers assigned",
      value: ov?.teachers_assigned ?? "…",
      hint: `${ov?.teacher_accounts ?? "…"} teacher accounts · ${ov?.courses_without_teachers ?? "…"} subjects unstaffed`,
    },
    {
      icon: "cloud_done",
      label: "Ingest",
      value: ov ? `${ov.ingest_summary.complete ?? 0}/${ov.materials}` : "…",
      hint: "materials embedded and quotable",
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-gutter md:p-section-gap ns-custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-section-gap pb-32">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="font-display-lg text-display-lg text-on-surface mb-2">Dashboard</h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant">
              The institution at a glance — batches, subjects, materials and staffing.
            </p>
          </div>
          <button
            onClick={() => setModalOpen(true)}
            className="ns-btn-primary font-label-md text-label-md px-5 py-3 rounded-lg flex items-center gap-2"
          >
            <Icon name="add" />
            Add new batch
          </button>
        </div>

        {error && (
          <p role="alert" className="bg-error/15 text-on-surface px-5 py-4 rounded-lg font-body-md">
            {error}
          </p>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter">
          {tiles.map((t) => (
            <div key={t.label} className="ns-glass-panel rounded-xl p-card-inner-padding">
              <Icon name={t.icon} className="text-tertiary text-[22px] mb-3" />
              <p className="font-display-lg text-display-lg text-on-surface">{t.value}</p>
              <p className="font-label-md text-label-md text-on-surface mt-1">{t.label}</p>
              <p className="font-label-sm text-label-sm text-on-surface-variant mt-2">{t.hint}</p>
            </div>
          ))}
        </div>

        <section className="ns-glass-panel rounded-xl p-card-inner-padding">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
              <Icon name="collections_bookmark" className="text-tertiary" />
              Batches
            </h2>
            <button
              onClick={() => goToTab("batches")}
              className="font-label-md text-label-md text-tertiary hover:underline"
            >
              Manage batches →
            </button>
          </div>
          {batches.length === 0 ? (
            <p className="font-body-md text-on-surface-variant">
              No batches yet — create the first cohort with "Add new batch".
            </p>
          ) : (
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {batches.slice(0, 6).map((b) => (
                <li
                  key={b.id}
                  className="bg-surface-container-low/50 rounded-lg p-4 border border-outline-variant/20"
                >
                  <p className="font-headline-sm text-headline-sm text-on-surface">
                    {MAJOR_LABELS[b.major]} · {b.department.name}
                  </p>
                  <p className="font-label-sm text-label-sm text-on-surface-variant mt-1">
                    {b.start_year}–{b.end_year} ·{" "}
                    {b.curriculum ? (
                      <span className="text-tertiary">curriculum attached</span>
                    ) : (
                      "no curriculum yet"
                    )}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {modalOpen && (
        <NewBatchModal
          onClose={() => setModalOpen(false)}
          onDone={() => {
            setModalOpen(false);
            load();
          }}
          goToBatches={() => {
            setModalOpen(false);
            goToTab("batches");
          }}
        />
      )}
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* The 3-step "add batch" modal                                              */
/* ------------------------------------------------------------------------ */

export function NewBatchModal({
  onClose,
  onDone,
  goToBatches,
}: {
  onClose: () => void;
  onDone: () => void;
  goToBatches: () => void;
}) {
  // step 1: the cohort; step 2: the curriculum; step 3: where to go next
  const [step, setStep] = useState(1);
  const [major, setMajor] = useState("btech");
  const [departmentId, setDepartmentId] = useState<number | null>(null);
  const [startYear, setStartYear] = useState(String(THIS_YEAR + 1));
  const [departments, setDepartments] = useState<{ id: number; name: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [batch, setBatch] = useState<BatchDto | null>(null);

  // reuse candidates: earlier batches, same major + department, with a curriculum
  const [allBatches, setAllBatches] = useState<BatchDto[]>([]);

  useEffect(() => {
    listDepartments()
      .then((r) => {
        setDepartments(r.items);
        setDepartmentId((cur) => cur ?? r.items[0]?.id ?? null);
      })
      .catch(() => setError("Could not load departments."));
    getBatches().then(setAllBatches).catch(() => {});
  }, []);

  const endYear = Number(startYear) + (MAJOR_YEARS[major] ?? 0);
  const reuseCandidates = allBatches.filter(
    (b) =>
      b.major === major &&
      b.department.id === departmentId &&
      b.curriculum !== null &&
      b.start_year < Number(startYear),
  );

  async function createCohort() {
    setBusy(true);
    setError(null);
    try {
      const b = await createBatch(major, departmentId!, Number(startYear));
      setBatch(b);
      setStep(2);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function upload(file: File) {
    setBusy(true);
    setError(null);
    try {
      await uploadBatchCurriculum(batch!.id, file);
      setStep(3);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function reuse(fromId: number) {
    setBusy(true);
    setError(null);
    try {
      await reuseBatchCurriculum(batch!.id, fromId);
      setStep(3);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const fileRef = useRef<HTMLInputElement | null>(null);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Add a new batch"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="ns-glass-panel !bg-surface rounded-2xl w-full max-w-[34rem] p-8 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="font-headline-sm text-headline-sm text-on-surface">Add a new batch</h2>
          <div className="flex items-center gap-2 font-label-sm text-label-sm text-on-surface-variant">
            {[1, 2, 3].map((s) => (
              <span
                key={s}
                className={`w-7 h-7 rounded-full flex items-center justify-center border ${
                  s === step
                    ? "bg-tertiary text-on-tertiary border-tertiary"
                    : s < step
                      ? "border-tertiary text-tertiary"
                      : "border-outline-variant"
                }`}
              >
                {s < step ? "✓" : s}
              </span>
            ))}
          </div>
        </div>

        {step === 1 && (
          <div className="space-y-5">
            <div>
              <label className="font-label-md text-label-md text-on-surface-variant block mb-2">
                Major
              </label>
              <div className="grid grid-cols-4 gap-2">
                {Object.keys(MAJOR_YEARS).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMajor(m)}
                    className={`py-3 rounded-lg font-label-md text-label-md border transition-colors ${
                      m === major
                        ? "border-tertiary text-tertiary bg-tertiary/10"
                        : "border-outline-variant text-on-surface hover:border-tertiary/50"
                    }`}
                  >
                    {MAJOR_LABELS[m]}
                    <span className="block font-label-sm text-label-sm text-on-surface-variant">
                      {MAJOR_YEARS[m]} yrs
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="font-label-md text-label-md text-on-surface-variant block mb-2">
                Department
              </label>
              <select
                value={departmentId ?? ""}
                onChange={(e) => setDepartmentId(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface"
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-label-md text-label-md text-on-surface-variant block mb-2">
                Starting year
              </label>
              <input
                type="number"
                min={2000}
                max={2100}
                value={startYear}
                onChange={(e) => setStartYear(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface"
              />
              <p className="font-label-sm text-label-sm text-tertiary mt-2">
                {MAJOR_LABELS[major]} runs {startYear || "…"}–{endYear || "…"} (
                {MAJOR_YEARS[major]} years) — the duration is fixed by the major.
              </p>
            </div>

            {error && <p role="alert" className="text-error font-body-sm">{error}</p>}

            <button
              onClick={createCohort}
              disabled={busy || !departmentId || !startYear}
              className="ns-btn-primary w-full font-label-md text-label-md px-5 py-3 rounded-lg disabled:opacity-50"
            >
              {busy ? "Creating…" : "Create batch"}
            </button>
          </div>
        )}

        {step === 2 && batch && (
          <div className="space-y-5">
            <p className="font-body-md text-on-surface">
              <strong>
                {MAJOR_LABELS[batch.major]} · {batch.department.name} {batch.start_year}–
                {batch.end_year}
              </strong>{" "}
              created. Now the curriculum:
            </p>

            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload(f);
              }}
            />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={busy}
              className="ns-btn-primary w-full font-label-md text-label-md px-5 py-3 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Icon name="upload_file" />
              {busy ? "Uploading…" : "Upload curriculum (PDF / DOCX)"}
            </button>

            <div className="flex items-center gap-3 font-label-sm text-label-sm text-on-surface-variant">
              <span className="flex-1 border-t border-outline-variant/40" /> or reuse{" "}
              <span className="flex-1 border-t border-outline-variant/40" />
            </div>

            {reuseCandidates.length === 0 ? (
              <button
                disabled
                title="No earlier batch of this major and department has a curriculum to reuse."
                className="w-full font-label-md text-label-md px-5 py-3 rounded-lg border border-outline-variant/40 text-on-surface-variant opacity-50 cursor-not-allowed"
              >
                Reuse a previous year's curriculum
              </button>
            ) : (
              <div className="space-y-2">
                {reuseCandidates.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => reuse(c.id)}
                    disabled={busy}
                    className="w-full text-left px-4 py-3 rounded-lg border border-outline-variant hover:border-tertiary font-label-md text-label-md text-on-surface flex items-center justify-between disabled:opacity-50"
                  >
                    <span>
                      Reuse {c.start_year}–{c.end_year}
                    </span>
                    <span className="font-label-sm text-label-sm text-on-surface-variant truncate max-w-[14rem]">
                      {c.curriculum?.name}
                    </span>
                  </button>
                ))}
              </div>
            )}

            <button
              onClick={() => setStep(3)}
              className="w-full font-label-md text-label-md text-on-surface-variant hover:text-tertiary py-2"
            >
              Skip for now
            </button>
            {error && <p role="alert" className="text-error font-body-sm">{error}</p>}
          </div>
        )}

        {step === 3 && batch && (
          <div className="space-y-5 text-center">
            <Icon name="check_circle" className="text-tertiary text-[48px]" />
            <p className="font-body-lg text-on-surface">
              {MAJOR_LABELS[batch.major]} · {batch.department.name} {batch.start_year}–
              {batch.end_year} is set up
              {batch.curriculum ? " with its curriculum." : " (curriculum can be added later)."}
            </p>
            <p className="font-body-md text-on-surface-variant">
              Next: go to the <strong>Batches</strong> tab to add the subjects and materials for
              the batch's department.
            </p>
            <button
              onClick={goToBatches}
              className="ns-btn-primary w-full font-label-md text-label-md px-5 py-3 rounded-lg"
            >
              Go to Batches
            </button>
            <button onClick={onDone} className="font-label-md text-label-md text-on-surface-variant hover:text-tertiary">
              Stay on the dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Batches tab                                                               */
/* ------------------------------------------------------------------------ */

export function BatchesView({ goToTab }: { goToTab: (t: AdminTabKey) => void }) {
  // the subjects tab's key is historical: "structure" predates the rename to
  // "Subjects & Materials"
  const [batches, setBatches] = useState<BatchDto[] | null>(null);
  // admin-010: which cohort's subject list is open
  const [openSubjects, setOpenSubjects] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const fileFor = useRef<HTMLInputElement | null>(null);
  const [uploadTarget, setUploadTarget] = useState<number | null>(null);

  const load = () =>
    getBatches()
      .then((b) => {
        setBatches(b);
        setError(null);
      })
      .catch((err) => setError(errorText(err)));

  useEffect(() => {
    load();
  }, []);

  async function doUpload(file: File) {
    if (uploadTarget === null) return;
    setBusyId(uploadTarget);
    try {
      await uploadBatchCurriculum(uploadTarget, file);
      await load();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusyId(null);
      setUploadTarget(null);
    }
  }

  async function doReuse(target: BatchDto, from: BatchDto) {
    setBusyId(target.id);
    try {
      await reuseBatchCurriculum(target.id, from.id);
      await load();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-gutter md:p-section-gap ns-custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-section-gap pb-32">
        <div>
          <h1 className="font-display-lg text-display-lg text-on-surface mb-2">Batches</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Cohorts and their curricula. Subjects and their materials live one tab over — a
            batch's department tells you which.
          </p>
        </div>

        <input
          ref={fileFor}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) doUpload(f);
          }}
        />

        {error && (
          <p role="alert" className="bg-error/15 text-on-surface px-5 py-4 rounded-lg font-body-md">
            {error}
          </p>
        )}

        {!batches ? (
          <p className="font-body-md text-on-surface-variant">Loading…</p>
        ) : batches.length === 0 ? (
          <p className="font-body-md text-on-surface-variant">
            No batches yet — create one from the Dashboard.
          </p>
        ) : (
          <div className="space-y-4">
            {batches.map((b) => {
              const candidates = batches.filter(
                (c) =>
                  c.major === b.major &&
                  c.department.id === b.department.id &&
                  c.curriculum !== null &&
                  c.start_year < b.start_year,
              );
              return (
                <article key={b.id} className="ns-glass-panel rounded-xl p-card-inner-padding">
                  <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-8">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-headline-sm text-headline-sm text-on-surface">
                      {MAJOR_LABELS[b.major]} · {b.department.name}
                    </h3>
                    <p className="font-label-sm text-label-sm text-on-surface-variant mt-1">
                      {b.start_year}–{b.end_year} · {b.course_count} subject
                      {b.course_count === 1 ? "" : "s"}
                    </p>
                  </div>

                  <div className="flex-1 min-w-0">
                    {b.curriculum ? (
                      <p className="font-label-md text-label-md text-tertiary flex items-center gap-2 truncate">
                        <Icon name="description" />
                        {b.curriculum.name}
                        {b.curriculum.reused_from_batch_id !== null && (
                          <span className="text-on-surface-variant">
                            (reused from batch #{b.curriculum.reused_from_batch_id})
                          </span>
                        )}
                      </p>
                    ) : (
                      <p className="font-label-md text-label-md text-on-surface-variant">
                        No curriculum attached
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => setOpenSubjects((cur) => (cur === b.id ? null : b.id))}
                      className="font-label-md text-label-md px-4 py-2 rounded-lg border border-outline-variant hover:border-tertiary text-on-surface"
                    >
                      {openSubjects === b.id ? "Hide subjects" : "Subjects"}
                    </button>
                    <button
                      onClick={() => {
                        setUploadTarget(b.id);
                        fileFor.current?.click();
                      }}
                      disabled={busyId === b.id}
                      className="font-label-md text-label-md px-4 py-2 rounded-lg border border-outline-variant hover:border-tertiary text-on-surface disabled:opacity-50"
                    >
                      {b.curriculum ? "Replace" : "Upload"}
                    </button>
                    {candidates.length > 0 && !b.curriculum && (
                      <button
                        onClick={() => doReuse(b, candidates[0])}
                        disabled={busyId === b.id}
                        title={`Reuse ${candidates[0].start_year}–${candidates[0].end_year} (${candidates[0].curriculum?.name})`}
                        className="font-label-md text-label-md px-4 py-2 rounded-lg border border-outline-variant hover:border-tertiary text-on-surface disabled:opacity-50"
                      >
                        Reuse {candidates[0].start_year}
                      </button>
                    )}
                    </div>
                  </div>
                  {openSubjects === b.id && <BatchSubjects batch={b} onChanged={load} />}
                </article>
              );
            })}
          </div>
        )}

        <button
          onClick={() => goToTab("structure")}
          className="font-label-md text-label-md text-tertiary hover:underline"
        >
          Add subjects and materials →
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Subjects in a batch (admin-010)                                           */
/* ------------------------------------------------------------------------ */

function BatchSubjects({ batch, onChanged }: { batch: BatchDto; onChanged: () => void }) {
  const [items, setItems] = useState<BatchCourse[] | null>(null);
  const [all, setAll] = useState<Course[]>([]);
  const [mode, setMode] = useState<"none" | "existing" | "new">("none");
  const [pick, setPick] = useState<number | "">("");
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [semester, setSemester] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () =>
    getBatchCourses(batch.id)
      .then((r) => {
        setItems(r);
        setError(null);
      })
      .catch((err) => setError(errorText(err)));

  useEffect(() => {
    load();
    listCourses().then((r) => setAll(r.items)).catch(() => setAll([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [batch.id]);

  async function add() {
    setBusy(true);
    setError(null);
    try {
      if (mode === "existing") {
        if (pick === "") return;
        await addBatchCourse(batch.id, { course_id: Number(pick) });
      } else {
        if (!code.trim() || !title.trim()) return;
        await addBatchCourse(batch.id, {
          code: code.trim(),
          title: title.trim(),
          ...(semester ? { semester: Number(semester) } : {}),
        });
      }
      setPick("");
      setCode("");
      setTitle("");
      setSemester("");
      setMode("none");
      await load();
      onChanged();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove(courseId: number) {
    setBusy(true);
    try {
      await removeBatchCourse(batch.id, courseId);
      await load();
      onChanged();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const linked = new Set((items ?? []).map((c) => c.id));
  const available = all.filter((c) => !linked.has(c.id));

  return (
    <div className="mt-4 pt-4 border-t border-outline-variant/20 space-y-3">
      {error && <p role="alert" className="text-error font-body-sm">{error}</p>}

      {!items ? (
        <p className="font-label-sm text-label-sm text-on-surface-variant">Loading subjects…</p>
      ) : items.length === 0 ? (
        <p className="font-label-sm text-label-sm text-on-surface-variant">
          No subjects in this batch yet.
        </p>
      ) : (
        <ul className="space-y-2">
          {items.map((c) => (
            <li
              key={c.id}
              className="flex items-center justify-between gap-3 bg-surface-container-low/50 rounded-lg px-4 py-2.5 border border-outline-variant/20"
            >
              <span className="min-w-0 font-label-md text-label-md text-on-surface truncate">
                <span className="text-tertiary">{c.code}</span> · {c.title}
                {c.semester !== null && (
                  <span className="text-on-surface-variant"> · sem {c.semester}</span>
                )}
                {c.batch_ids.length > 1 && (
                  <span
                    className="text-on-surface-variant"
                    title="This subject is shared with other cohorts; removing it here leaves those untouched."
                  >
                    {" "}· shared with {c.batch_ids.length - 1} other cohort
                    {c.batch_ids.length - 1 === 1 ? "" : "s"}
                  </span>
                )}
              </span>
              <button
                onClick={() => remove(c.id)}
                disabled={busy}
                title="Unlink from this batch. The subject and its materials are kept."
                className="font-label-sm text-label-sm text-on-surface-variant hover:text-error shrink-0"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}

      {mode === "none" && (
        <div className="flex gap-3">
          <button
            onClick={() => setMode("existing")}
            className="font-label-sm text-label-sm text-tertiary hover:underline"
          >
            + Add existing subject
          </button>
          <button
            onClick={() => setMode("new")}
            className="font-label-sm text-label-sm text-tertiary hover:underline"
          >
            + Create new subject
          </button>
        </div>
      )}

      {mode === "existing" && (
        <div className="flex flex-wrap gap-2 items-center">
          <select
            value={pick}
            onChange={(e) => setPick(e.target.value === "" ? "" : Number(e.target.value))}
            className="flex-1 min-w-[14rem] px-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface font-label-md text-label-md"
          >
            <option value="">Choose a subject…</option>
            {available.map((c) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.title}
              </option>
            ))}
          </select>
          <button
            onClick={add}
            disabled={busy || pick === ""}
            className="ns-btn-primary font-label-sm text-label-sm px-4 py-2 rounded-lg disabled:opacity-50"
          >
            {busy ? "…" : "Add"}
          </button>
          <button
            onClick={() => setMode("none")}
            className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface"
          >
            Cancel
          </button>
        </div>
      )}

      {mode === "new" && (
        <div className="flex flex-wrap gap-2 items-center">
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Code (CS301)"
            className="w-[9rem] px-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface font-label-md text-label-md"
          />
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="flex-1 min-w-[12rem] px-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface font-label-md text-label-md"
          />
          <input
            value={semester}
            onChange={(e) => setSemester(e.target.value)}
            placeholder="Sem"
            type="number"
            min={1}
            max={12}
            className="w-[5rem] px-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface font-label-md text-label-md"
          />
          <button
            onClick={add}
            disabled={busy || !code.trim() || !title.trim()}
            className="ns-btn-primary font-label-sm text-label-sm px-4 py-2 rounded-lg disabled:opacity-50"
          >
            {busy ? "…" : "Create"}
          </button>
          <button
            onClick={() => setMode("none")}
            className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface"
          >
            Cancel
          </button>
          <p className="w-full font-label-sm text-label-sm text-on-surface-variant">
            Created in {batch.department.name} — the batch's own department.
          </p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Teachers dialog (per subject)                                             */
/* ------------------------------------------------------------------------ */

export function TeachersDialog({ course, onClose }: { course: Course; onClose: () => void }) {
  const [teachers, setTeachers] = useState<AssignedTeacher[] | null>(null);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [issued, setIssued] = useState<{ email: string; password: string } | null>(null);

  const load = () =>
    getCourseTeachers(course.id)
      .then((t) => {
        setTeachers(t);
        setError(null);
      })
      .catch((err) => setError(errorText(err)));

  useEffect(() => {
    load();
  }, [course.id]);

  async function add() {
    if (!email.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const r = await addCourseTeacher(course.id, email.trim(), fullName.trim() || undefined);
      if (r.password) setIssued({ email: r.teacher.email, password: r.password });
      setEmail("");
      setFullName("");
      await load();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove(userId: number) {
    setBusy(true);
    try {
      await removeCourseTeacher(course.id, userId);
      await load();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`Teachers for ${course.title}`}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="ns-glass-panel !bg-surface rounded-2xl w-full max-w-[30rem] p-8 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="font-headline-sm text-headline-sm text-on-surface">
            Teachers · {course.code}
          </h2>
          <button onClick={onClose} className="text-on-surface-variant hover:text-on-surface">
            <Icon name="close" />
          </button>
        </div>

        {issued && (
          <div className="bg-tertiary/15 border border-tertiary/40 rounded-lg p-4 space-y-2">
            <p className="font-label-md text-label-md text-on-surface flex items-center gap-2">
              <Icon name="key" className="text-tertiary" />
              Password for {issued.email} — shown once, share it now:
            </p>
            <code className="font-label-lg text-label-lg text-tertiary select-all block">
              {issued.password}
            </code>
            <p className="font-label-sm text-label-sm text-on-surface-variant">
              It is never displayed again. They sign in at the unified login with this password.
            </p>
          </div>
        )}

        <div className="space-y-3">
          <input
            type="email"
            placeholder="teacher@example.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface"
          />
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Full name (optional)"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="flex-1 px-4 py-3 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface"
            />
            <button
              onClick={add}
              disabled={busy || !email.trim()}
              className="ns-btn-primary font-label-md text-label-md px-5 rounded-lg disabled:opacity-50"
            >
              {busy ? "…" : "Add"}
            </button>
          </div>
          <p className="font-label-sm text-label-sm text-on-surface-variant">
            A new email issues a teacher account with a generated password; an existing teacher is
            simply linked. No limit on how many.
          </p>
        </div>

        {error && <p role="alert" className="text-error font-body-sm">{error}</p>}

        <div className="space-y-2">
          {!teachers ? (
            <p className="font-body-md text-on-surface-variant">Loading…</p>
          ) : teachers.length === 0 ? (
            <p className="font-body-md text-on-surface-variant">No teachers assigned yet.</p>
          ) : (
            teachers.map((t) => (
              <div
                key={t.user_id}
                className="flex items-center justify-between gap-3 bg-surface-container-low/50 rounded-lg px-4 py-3 border border-outline-variant/20"
              >
                <div className="min-w-0">
                  <p className="font-label-md text-label-md text-on-surface truncate">
                    {t.full_name}
                  </p>
                  <p className="font-label-sm text-label-sm text-on-surface-variant truncate">
                    {t.email}
                  </p>
                </div>
                <button
                  onClick={() => remove(t.user_id)}
                  disabled={busy}
                  className="font-label-sm text-label-sm text-on-surface-variant hover:text-error shrink-0"
                >
                  Unassign
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
