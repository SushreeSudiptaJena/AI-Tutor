import React, { useEffect, useState } from "react";
import {
  ApiError,
  archiveMaterial,
  deleteMaterial,
  getMe,
  listAuditLog,
  listCourses,
  listDepartments,
  listMaterials,
  uploadMaterial,
} from "@/lib/api";
import type {
  AuditRow,
  Course,
  Department,
  Material,
  MaterialKind,
  User,
} from "@/lib/api";

/**
 * AdminDashboard.tsx
 * ---------------------------------------------------------------------------
 * The three admin screens (Curriculum Upload, Course Structure, Audit Log)
 * under one component with client-side tab navigation.
 *
 * Every panel reads the live backend. Nothing here is placeholder data: the
 * course list is `GET /admin/courses`, the material list is
 * `GET /admin/courses/{id}/materials`, the log is `GET /admin/audit-log`.
 * If a panel is empty, the database is empty -- that distinction has to stay
 * visible, which is why each panel has a real empty state rather than a
 * plausible-looking row.
 *
 * STYLING: every token used here (`bg-surface`, `text-tertiary`,
 * `p-card-inner-padding`, `text-display-lg`) is defined in the @theme block
 * of src/index.css and compiled by the project's own Tailwind. There is no
 * runtime CDN: see the note at the bottom of index.css for why that matters.
 * ---------------------------------------------------------------------------
 */

type TabKey = "upload" | "structure" | "audit";

const NAV_ITEMS: { key: TabKey; label: string; icon: string }[] = [
  { key: "upload", label: "Curriculum Upload", icon: "cloud_upload" },
  { key: "structure", label: "Course Structure", icon: "account_tree" },
  { key: "audit", label: "Audit Log", icon: "receipt_long" },
];

/** The closed list the backend accepts -- admin-007 added `reference`. */
const MATERIAL_KINDS: { value: MaterialKind; label: string }[] = [
  { value: "textbook", label: "Textbook" },
  { value: "syllabus", label: "Syllabus" },
  { value: "assignment", label: "Assignment" },
  { value: "reference", label: "Reference" },
];

function useLiveClock() {
  const [clock, setClock] = useState(() => formatClock());
  useEffect(() => {
    const id = setInterval(() => setClock(formatClock()), 30_000);
    return () => clearInterval(id);
  }, []);
  return clock;
}

function formatClock() {
  const now = new Date();
  const dateStr = now.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const timeStr = now.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" });
  return `${dateStr} | ${timeStr}`;
}

/** ISO timestamp -> "2h ago". Falls back to the raw date past a week. */
function relativeTime(iso: string | null): string {
  if (!iso) return "unknown time";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "unknown time";
  const mins = Math.round((Date.now() - then) / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Try again.";
}

function Icon({ name, filled = false, className = "" }: { name: string; filled?: boolean; className?: string }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={filled ? ({ fontVariationSettings: "'FILL' 1" } as React.CSSProperties) : undefined}
    >
      {name}
    </span>
  );
}

/** One place for the three states every panel has, so none of them forgets one. */
function Panel({
  loading,
  error,
  empty,
  emptyText,
  children,
}: {
  loading: boolean;
  error: string | null;
  empty?: boolean;
  emptyText?: string;
  children: React.ReactNode;
}) {
  if (loading) {
    return (
      <p className="font-body-md text-body-md text-on-surface-variant py-6">Loading…</p>
    );
  }
  if (error) {
    return (
      <p role="alert" className="font-body-md text-body-md text-error py-6">
        {error}
      </p>
    );
  }
  if (empty) {
    return (
      <p className="font-body-md text-body-md text-on-surface-variant py-6">
        {emptyText ?? "Nothing here yet."}
      </p>
    );
  }
  return <>{children}</>;
}

function Sidebar({ active, onSelect }: { active: TabKey; onSelect: (k: TabKey) => void }) {
  return (
    <nav className="bg-surface-container-low h-full w-64 fixed left-0 top-0 border-r border-outline-variant/10 shadow-sm flex flex-col py-container-padding z-40">
      <div className="px-gutter mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-full bg-surface-container-highest border border-outline-variant/30 flex items-center justify-center text-tertiary font-bold">
            NS
          </div>
          <div>
            <h1 className="font-headline-md text-headline-md font-bold text-on-surface">Nocturnal Scholar</h1>
            <p className="font-label-sm text-label-sm text-on-surface-variant">Admin Console</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-2 px-4 flex-grow">
        {NAV_ITEMS.map((item) => {
          const isActive = item.key === active;
          return (
            <button
              key={item.key}
              onClick={() => onSelect(item.key)}
              className={
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-colors duration-200 text-left " +
                (isActive
                  ? "text-tertiary bg-tertiary-container/20"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50")
              }
            >
              <Icon name={item.icon} filled={isActive} />
              <span className="font-label-md text-label-md">{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-2 px-4 mt-auto pt-6 border-t border-outline-variant/10">
        <a className="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 transition-colors duration-200 rounded-xl" href="#">
          <Icon name="settings" />
          <span className="font-label-md text-label-md">Settings</span>
        </a>
        <a className="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 transition-colors duration-200 rounded-xl" href="#">
          <Icon name="help" />
          <span className="font-label-md text-label-md">Support</span>
        </a>
      </div>
    </nav>
  );
}

function TopBar({ title, user }: { title: string; user: User | null }) {
  const clock = useLiveClock();
  return (
    <header className="bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10 sticky top-0 flex justify-between items-center w-full px-gutter h-16 z-30">
      <h2 className="font-headline-sm text-headline-sm font-bold text-on-surface">{title}</h2>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-on-surface-variant font-label-md text-label-md">
          <Icon name="schedule" className="text-[18px]" />
          <span>{clock}</span>
        </div>
        <div className="w-px h-6 bg-outline-variant/30" />
        <div className="flex items-center gap-4">
          <button className="text-on-surface-variant hover:text-tertiary transition-colors">
            <Icon name="notifications" />
          </button>
          <div className="flex items-center gap-3 ml-2">
            {/* The signed-in admin, not a stand-in name. */}
            <span className="font-label-md text-label-md text-tertiary">
              {user ? user.full_name : "…"}
            </span>
            <div className="w-8 h-8 rounded-full bg-surface-container-highest border border-outline-variant/30 flex items-center justify-center text-on-surface-variant">
              <Icon name="account_circle" filled />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

/* ------------------------------------------------------------------------ */
/* Tab 1: Curriculum Upload                                                  */
/* ------------------------------------------------------------------------ */

function CurriculumUploadView({ courses, coursesError }: { courses: Course[]; coursesError: string | null }) {
  const [courseId, setCourseId] = useState<number | null>(null);
  const [kind, setKind] = useState<MaterialKind>("textbook");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [materials, setMaterials] = useState<Material[]>([]);
  const [loadingMaterials, setLoadingMaterials] = useState(false);
  const [materialsError, setMaterialsError] = useState<string | null>(null);

  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Default to the first course once the list arrives.
  useEffect(() => {
    if (courseId === null && courses.length) setCourseId(courses[0].id);
  }, [courses, courseId]);

  function refreshMaterials(id: number) {
    setLoadingMaterials(true);
    setMaterialsError(null);
    listMaterials(id, true)
      .then((r) => setMaterials(r.items))
      .catch((err) => setMaterialsError(errorText(err)))
      .finally(() => setLoadingMaterials(false));
  }

  useEffect(() => {
    if (courseId === null) return;
    refreshMaterials(courseId);
  }, [courseId]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    setUploadError(null);
    setNotice(null);
    if (courseId === null) return setUploadError("Pick a target course first.");
    if (!file) return setUploadError("Choose a file to upload.");
    if (!title.trim()) return setUploadError("Give the material a title.");

    setBusy(true);
    try {
      const m = await uploadMaterial(courseId, file, kind, title.trim());
      setNotice(`Uploaded “${m.title}” as version ${m.version}. Ingestion runs separately.`);
      setFile(null);
      setTitle("");
      refreshMaterials(courseId);
    } catch (err) {
      setUploadError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleArchive(m: Material) {
    setNotice(null);
    setUploadError(null);
    try {
      await archiveMaterial(m.id);
      setNotice(`Archived “${m.title}”.`);
      if (courseId !== null) refreshMaterials(courseId);
    } catch (err) {
      setUploadError(errorText(err));
    }
  }

  async function handleDelete(m: Material) {
    setNotice(null);
    setUploadError(null);
    try {
      await deleteMaterial(m.id);
      setNotice(`Deleted “${m.title}”. The source file is still on disk.`);
      if (courseId !== null) refreshMaterials(courseId);
    } catch (err) {
      // admin-006 returns 409 mid_term with a message that tells the admin to
      // archive instead. Surfacing it verbatim is the whole point of the guard.
      setUploadError(errorText(err));
    }
  }

  const totalChunks = materials.reduce((n, m) => n + (m.chunk_count || 0), 0);
  const activeCount = materials.filter((m) => m.status === "active").length;

  return (
    <div className="flex-1 overflow-y-auto p-gutter md:p-section-gap ns-custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-section-gap pb-32">
        <div>
          <h1 className="font-display-lg text-display-lg text-on-surface mb-2">Curriculum Upload</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Ingest, version, and map scholarly texts to course structures.
          </p>
        </div>

        {notice && (
          <p className="font-body-md text-body-md text-tertiary bg-tertiary-container/20 border border-tertiary/20 rounded-lg px-4 py-3">
            {notice}
          </p>
        )}
        {uploadError && (
          <p role="alert" className="font-body-md text-body-md text-error bg-error/10 border border-error/20 rounded-lg px-4 py-3">
            {uploadError}
          </p>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
          <div className="lg:col-span-7 flex flex-col gap-gutter">
            <form onSubmit={handleUpload} className="contents">
              <section className="ns-glass-panel rounded-xl p-card-inner-padding">
                <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4 flex items-center gap-2">
                  <Icon name="upload_file" className="text-tertiary" />
                  Source Material Ingestion
                </h2>

                <label
                  htmlFor="material-file"
                  className="border-2 border-dashed border-outline-variant/50 rounded-lg p-8 flex flex-col items-center justify-center text-center bg-surface-container-low/30 hover:bg-surface-container-low/60 hover:border-tertiary/50 transition-all cursor-pointer group"
                >
                  <div className="bg-surface-container-high p-4 rounded-full mb-4 group-hover:scale-110 transition-transform shadow-lg shadow-black/20">
                    <Icon name="note_add" className="text-3xl text-on-surface-variant group-hover:text-tertiary transition-colors" />
                  </div>
                  <h3 className="font-headline-md text-headline-md text-on-surface mb-2">
                    {file ? file.name : "Choose a document"}
                  </h3>
                  <p className="font-body-md text-body-md text-on-surface-variant mb-6 max-w-sm">
                    PDF, DOCX, TXT and MD are accepted. The ingester reads what the
                    uploader accepts — nothing can be stored that cannot later be ingested.
                  </p>
                  <span className="px-6 py-2.5 bg-surface-container-high text-on-surface font-label-md text-label-md rounded-full border border-outline-variant/30 hover:bg-surface-bright transition-colors flex items-center gap-2 shadow-sm">
                    Browse Files
                  </span>
                  <input
                    id="material-file"
                    type="file"
                    className="sr-only"
                    accept=".pdf,.docx,.txt,.md"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  />
                </label>
              </section>

              <section className="ns-glass-panel rounded-xl p-card-inner-padding">
                <h2 className="font-headline-sm text-headline-sm text-on-surface mb-6 flex items-center gap-2">
                  <Icon name="account_tree" className="text-tertiary" />
                  Content Mapping Strategy
                </h2>

                <div className="space-y-5">
                  <div>
                    <label htmlFor="target-course" className="block font-label-md text-label-md text-on-surface-variant mb-2">
                      Target Course
                    </label>
                    <select
                      id="target-course"
                      value={courseId ?? ""}
                      onChange={(e) => setCourseId(Number(e.target.value))}
                      disabled={!courses.length}
                      className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-4 py-2.5 font-body-md text-body-md text-on-surface focus:border-tertiary focus:ring-1 focus:ring-tertiary outline-none"
                    >
                      {!courses.length && <option value="">No courses yet</option>}
                      {courses.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.title} ({c.code})
                        </option>
                      ))}
                    </select>
                    {coursesError && (
                      <p role="alert" className="mt-2 font-label-sm text-label-sm text-error">
                        {coursesError}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="material-title" className="block font-label-md text-label-md text-on-surface-variant mb-2">
                        Title
                      </label>
                      <input
                        id="material-title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g. Django 5 By Example"
                        className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-4 py-2.5 font-body-md text-body-md text-on-surface placeholder-on-surface-variant focus:border-tertiary focus:ring-1 focus:ring-tertiary outline-none"
                      />
                    </div>
                    <div>
                      <label htmlFor="material-kind" className="block font-label-md text-label-md text-on-surface-variant mb-2">
                        Content Type
                      </label>
                      <select
                        id="material-kind"
                        value={kind}
                        onChange={(e) => setKind(e.target.value as MaterialKind)}
                        className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-4 py-2.5 font-body-md text-body-md text-on-surface focus:border-tertiary focus:ring-1 focus:ring-tertiary outline-none"
                      >
                        {MATERIAL_KINDS.map((k) => (
                          <option key={k.value} value={k.value}>
                            {k.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="pt-4 flex justify-end">
                    <button
                      type="submit"
                      disabled={busy}
                      className="px-6 py-2.5 ns-btn-primary font-label-md text-label-md rounded-full transition-all flex items-center gap-2 disabled:opacity-60"
                    >
                      <Icon name="add_link" className="text-sm" />
                      {busy ? "Uploading…" : "Upload to course"}
                    </button>
                  </div>
                </div>
              </section>
            </form>
          </div>

          <div className="lg:col-span-5 flex flex-col gap-gutter">
            <section className="ns-glass-panel rounded-xl p-card-inner-padding h-full flex flex-col">
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-6 flex items-center gap-2">
                <Icon name="history" className="text-tertiary" />
                Repository Status
              </h2>

              <div className="space-y-4 flex-1">
                <div className="bg-surface-container-low/50 p-4 rounded-lg border border-outline-variant/20 flex items-center gap-4">
                  <div className="bg-tertiary/10 p-3 rounded-full">
                    <Icon name="storage" className="text-tertiary" />
                  </div>
                  <div>
                    <p className="font-label-md text-label-md text-on-surface-variant">Indexed for retrieval</p>
                    <p className="font-headline-md text-headline-md text-on-surface">
                      {totalChunks.toLocaleString()}{" "}
                      <span className="font-body-md text-body-md text-on-surface-variant">
                        chunks · {activeCount} active {activeCount === 1 ? "material" : "materials"}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-outline-variant/10">
                  <h3 className="font-label-md text-label-md text-on-surface-variant mb-4 uppercase tracking-wider">
                    Materials in this course
                  </h3>

                  <Panel
                    loading={loadingMaterials}
                    error={materialsError}
                    empty={!materials.length}
                    emptyText="No material uploaded to this course yet."
                  >
                    <ul className="space-y-3">
                      {materials.map((m) => (
                        <li key={m.id} className="flex items-start gap-3">
                          <div
                            className={
                              "w-1.5 h-1.5 rounded-full mt-2 " +
                              (m.ingest_status === "complete" ? "bg-tertiary" : "bg-outline")
                            }
                          />
                          <div className="flex-1 min-w-0">
                            <p className="font-body-md text-body-md text-on-surface text-sm truncate">
                              {m.title}{" "}
                              <span className="text-on-surface-variant">v{m.version}</span>
                            </p>
                            <p className="font-label-sm text-label-sm text-on-surface-variant">
                              {m.kind} · {m.status} · ingest {m.ingest_status} ·{" "}
                              {m.chunk_count.toLocaleString()} chunks
                            </p>
                            <p className="font-label-sm text-label-sm text-on-surface-variant">
                              {m.uploaded_by ?? "unknown uploader"} • {relativeTime(m.uploaded_at)}
                            </p>
                            <div className="flex gap-3 mt-1">
                              {m.status === "active" && (
                                <button
                                  onClick={() => handleArchive(m)}
                                  className="font-label-sm text-label-sm text-on-surface-variant hover:text-tertiary transition-colors"
                                >
                                  Archive
                                </button>
                              )}
                              <button
                                onClick={() => handleDelete(m)}
                                className="font-label-sm text-label-sm text-on-surface-variant hover:text-error transition-colors"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </Panel>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Tab 2: Course Structure                                                   */
/* ------------------------------------------------------------------------ */

function CourseStructureView({
  courses,
  loading,
  error,
}: {
  courses: Course[];
  loading: boolean;
  error: string | null;
}) {
  const [departments, setDepartments] = useState<Department[]>([]);

  useEffect(() => {
    listDepartments()
      .then((r) => setDepartments(r.items))
      .catch(() => setDepartments([]));
  }, []);

  const deptName = (id: number | null) =>
    departments.find((d) => d.id === id)?.name ?? "Unassigned";

  return (
    <div className="flex-1 overflow-y-auto p-gutter md:p-section-gap ns-custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-section-gap pb-32">
        <div>
          <h1 className="font-display-lg text-display-lg text-on-surface mb-2">Course Structure</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Departments, courses, prerequisites and teaching windows.
          </p>
        </div>

        <section className="ns-glass-panel rounded-xl p-card-inner-padding">
          <h2 className="font-headline-sm text-headline-sm text-on-surface mb-6 flex items-center gap-2">
            <Icon name="account_tree" className="text-tertiary" />
            Courses
          </h2>

          <Panel loading={loading} error={error} empty={!courses.length} emptyText="No courses defined yet.">
            <div className="space-y-4">
              {courses.map((c) => (
                <article
                  key={c.id}
                  className="bg-surface-container-low/50 p-4 rounded-lg border border-outline-variant/20"
                >
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface">
                        {c.title}{" "}
                        <span className="font-label-md text-label-md text-tertiary">{c.code}</span>
                      </h3>
                      <p className="font-label-sm text-label-sm text-on-surface-variant mt-1">
                        {deptName(c.department_id)}
                        {c.semester !== null && <> · semester {c.semester}</>}
                        {c.admission_batches.length > 0 && (
                          <> · batches {c.admission_batches.join(", ")}</>
                        )}
                      </p>
                    </div>

                    {/* admin-005/006: the term window is what the delete guard
                        reads, so it is stated plainly rather than implied. */}
                    <p className="font-label-sm text-label-sm text-on-surface-variant">
                      {c.term_start && c.term_end ? (
                        <>
                          Term {c.term_start} → {c.term_end}
                        </>
                      ) : (
                        <span title="No dates means no protected window: ingested material can be deleted at any time.">
                          No term window set
                        </span>
                      )}
                    </p>
                  </div>

                  <p className="font-body-md text-body-md text-on-surface-variant mt-3">
                    {c.prerequisite_courses.length ? (
                      <>
                        Prerequisites:{" "}
                        {c.prerequisite_courses.map((p) => `${p.title} (${p.code})`).join(", ")}
                      </>
                    ) : (
                      "No prerequisites."
                    )}
                  </p>
                </article>
              ))}
            </div>
          </Panel>
        </section>

        <section className="ns-glass-panel rounded-xl p-card-inner-padding">
          <h2 className="font-headline-sm text-headline-sm text-on-surface mb-6 flex items-center gap-2">
            <Icon name="apartment" className="text-tertiary" />
            Departments
          </h2>
          <Panel
            loading={false}
            error={null}
            empty={!departments.length}
            emptyText="No departments defined yet."
          >
            <ul className="flex flex-wrap gap-3">
              {departments.map((d) => (
                <li
                  key={d.id}
                  className="px-4 py-2 rounded-full bg-surface-container-low border border-outline-variant/30 font-label-md text-label-md text-on-surface"
                >
                  {d.name}
                </li>
              ))}
            </ul>
          </Panel>
        </section>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Tab 3: Audit Log                                                          */
/* ------------------------------------------------------------------------ */

function AuditLogView() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actor, setActor] = useState("");
  const [includeSystem, setIncludeSystem] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    // Debounced so typing in the actor box doesn't fire a request per keystroke.
    const id = setTimeout(() => {
      setLoading(true);
      setError(null);
      listAuditLog({ limit: 50, actor: actor.trim() || undefined, includeSystem })
        .then((r) => {
          setRows(r.items);
          setTotal(r.total);
        })
        .catch((err) => setError(errorText(err)))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(id);
  }, [actor, includeSystem]);

  return (
    <div className="flex-1 overflow-y-auto p-gutter md:p-section-gap ns-custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-section-gap pb-32">
        <div>
          <h1 className="font-display-lg text-display-lg text-on-surface mb-2">Audit Log</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Every approval in this system is an act by a named person. This is where that is legible.
          </p>
        </div>

        <section className="ns-glass-panel rounded-xl p-card-inner-padding">
          <div className="flex flex-wrap items-center gap-4 mb-6">
            <div className="relative flex-1 min-w-[240px]">
              <Icon
                name="search"
                className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]"
              />
              <input
                value={actor}
                onChange={(e) => setActor(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-full py-2 pl-10 pr-4 text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-tertiary focus:ring-1 focus:ring-tertiary font-body-md text-body-md transition-all"
                placeholder="Filter by actor email…"
              />
            </div>

            {/* admin-004: seed.run rows are hidden by default because a
                rehearsal day produced more of them than every real row. */}
            <label className="flex items-center gap-2 font-label-md text-label-md text-on-surface-variant cursor-pointer">
              <input
                type="checkbox"
                checked={includeSystem}
                onChange={(e) => setIncludeSystem(e.target.checked)}
                className="accent-[color:var(--color-tertiary)]"
              />
              Show system rows
            </label>

            <span className="font-label-sm text-label-sm text-on-surface-variant">
              {total.toLocaleString()} {total === 1 ? "entry" : "entries"}
            </span>
          </div>

          <Panel loading={loading} error={error} empty={!rows.length} emptyText="No audit entries match.">
            <ul className="divide-y divide-outline-variant/10">
              {rows.map((r) => (
                <li key={r.id} className="py-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      {/* Render `summary`; the machine fields stay behind
                          "details" because ?action= filters on them. */}
                      <p className="font-body-md text-body-md text-on-surface">{r.summary}</p>
                      <p className="font-label-sm text-label-sm text-on-surface-variant mt-0.5">
                        {new Date(r.at).toLocaleString()} · {r.action}
                      </p>
                    </div>
                    <button
                      onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                      className="font-label-sm text-label-sm text-on-surface-variant hover:text-tertiary transition-colors shrink-0"
                    >
                      {expanded === r.id ? "Hide" : "Details"}
                    </button>
                  </div>

                  {expanded === r.id && (
                    <pre className="mt-2 bg-surface-container-lowest/60 border border-outline-variant/20 rounded-lg p-3 overflow-x-auto font-label-sm text-label-sm text-on-surface-variant">
                      {JSON.stringify(
                        { action: r.action, target: r.target, actor: r.actor_email, detail: r.detail },
                        null,
                        2,
                      )}
                    </pre>
                  )}
                </li>
              ))}
            </ul>
          </Panel>
        </section>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Shell                                                                     */
/* ------------------------------------------------------------------------ */

const TITLES: Record<TabKey, string> = {
  upload: "Curriculum Upload",
  structure: "Course Structure",
  audit: "Audit Log",
};

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<TabKey>("upload");
  const [user, setUser] = useState<User | null>(null);

  // The course list is shared by two tabs, so it is fetched once here rather
  // than re-fetched every time somebody switches between them.
  const [courses, setCourses] = useState<Course[]>([]);
  const [coursesLoading, setCoursesLoading] = useState(true);
  const [coursesError, setCoursesError] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null));

    listCourses()
      .then((r) => setCourses(r.items))
      .catch((err) => setCoursesError(errorText(err)))
      .finally(() => setCoursesLoading(false));
  }, []);

  return (
    <div className="bg-surface min-h-screen text-on-surface font-sans">
      <Sidebar active={activeTab} onSelect={setActiveTab} />
      <div className="ml-64 flex flex-col min-h-screen">
        <TopBar title={TITLES[activeTab]} user={user} />
        {activeTab === "upload" && (
          <CurriculumUploadView courses={courses} coursesError={coursesError} />
        )}
        {activeTab === "structure" && (
          <CourseStructureView courses={courses} loading={coursesLoading} error={coursesError} />
        )}
        {activeTab === "audit" && <AuditLogView />}
      </div>
    </div>
  );
}
