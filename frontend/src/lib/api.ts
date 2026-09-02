/**
 * Every fetch in the app goes through this file. Nowhere else.
 *
 * Shapes here mirror docs/api-contract.md -- if that file changes, change this
 * one in the same commit.
 */

const BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "ai_tutor_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
// A token change is a user change: every cached read belongs to the previous
// session, so it never survives the swap (perf-002's one auth-boundary rule).
export const setToken = (t: string) => {
  localStorage.setItem(TOKEN_KEY, t);
  clearSessionCache();
};
export const clearToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  clearSessionCache();
};

/** The error envelope from the contract, thrown as a real Error. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public detail: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Options = { method?: string; body?: unknown; auth?: boolean };

export async function api<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  const { method = "GET", body, auth = true } = opts;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const token = getToken();
  if (auth && token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const parsed = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const e = parsed?.error ?? {};
    throw new ApiError(res.status, e.code ?? "unknown", e.message ?? res.statusText, e.detail ?? {});
  }
  return parsed as T;
}

/** multipart upload -- do not set Content-Type, the browser sets the boundary. */
export async function upload<T = unknown>(path: string, form: FormData): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  const text = await res.text();
  const parsed = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const e = parsed?.error ?? {};
    throw new ApiError(res.status, e.code ?? "unknown", e.message ?? res.statusText, e.detail ?? {});
  }
  return parsed as T;
}

// --- types from the contract's "Shared objects" section ---------------------

export type Role = "student" | "teacher" | "admin";

/** admin-009. A cohort: a major in a department, start year to the major's
 *  fixed end. The duration map is mirrored here for the modal's preview —
 *  the server computes end_year regardless of what the client says. */
export const MAJOR_YEARS: Record<string, number> = { btech: 4, bca: 3, mtech: 2, mca: 2 };

export type BatchDto = {
  id: number;
  major: string;
  department: { id: number; name: string };
  start_year: number;
  end_year: number;
  course_count: number;
  curriculum: { name: string; reused_from_batch_id: number | null } | null;
};

/** admin-010. A subject as a batch view needs it -- no prerequisite graph,
 *  no term window; those live on the full Course. */
export type BatchCourse = {
  id: number;
  code: string;
  title: string;
  department_id: number | null;
  semester: number | null;
  batch_ids: number[];
};

export type OverviewDto = {
  batches: number;
  courses_without_batch: number;
  departments: number;
  materials: number;
  courses: number;
  teachers_assigned: number;
  teacher_accounts: number;
  courses_without_teachers: number;
  ingest_summary: Record<string, number>;
};

export type AssignedTeacher = {
  user_id: number;
  email: string;
  full_name: string;
  assigned_at: string;
};

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  /** The ACTIVE subject: every scoped route reads this. */
  course_id?: number;
  /** student-010: the cohort a student was admitted to -- it decides which
   *  subjects are offered. Teachers have none. */
  batch_id?: number | null;
  preferred_language: string;
  university?: string | null;
  roll_number?: string | null;
};

export type Citation = {
  chunk_id: number;
  material_id: number;
  book_title: string;
  page_no: number;
  chapter?: string;
  snippet: string;
};

export type EvidenceReport = {
  alignment_score?: number;
  alignment_percent: number;
  top_similarity?: number;
  threshold?: number;
  sufficient: boolean;
  reason: string | null;
};

/**
 * Discriminated union -- ALWAYS branch on `outcome`.
 * All three arrive as HTTP 200: a refusal is a correct response, not an error.
 */
export type TutorResponse =
  | {
      outcome: "answered";
      language: string;
      body: string;
      citations: Citation[];
      evidence: EvidenceReport;
      /** tutor-003: present ONLY when a follow-up was rewritten into a
       * standalone question. Absent on the common case -- never render an
       * empty label. */
      resolved_question?: string;
    }
  | {
      outcome: "insufficient_evidence";
      language: string;
      body: string;
      citations: [];
      evidence: EvidenceReport;
      uncertainty_flag_id: number;
      /** tutor-003: present ONLY when a follow-up was rewritten into a
       * standalone question. Absent on the common case -- never render an
       * empty label. */
      resolved_question?: string;
      /** tutor-002: help from general knowledge, clearly labelled. The UI must
       * render it under its `note` warning — never with an alignment badge. */
      beyond_syllabus?: { body: string; note: string };
    }
  | {
      outcome: "graded_work_refused";
      language: string;
      body: string;
      hints: string[];
      citations: Citation[];
      matched_assignment: { material_id: number; title: string };
      /** tutor-003: present ONLY when a follow-up was rewritten into a
       * standalone question. Absent on the common case -- never render an
       * empty label. */
      resolved_question?: string;
    };

// --- baseline endpoints (infra-002) ----------------------------------------

export const getHealth = () => api<{ status: string; db: string }>("/health", { auth: false });

export const getProviderStatus = () =>
  api<{ active: string; fallbacks_available: string[]; cache_enabled: boolean }>(
    "/meta/provider-status",
  );

export const getLanguages = () =>
  api<{ items: { code: string; label: string }[] }>("/languages", { auth: false });

// --- auth endpoints (auth-001) ----------------------------------------

export const login = (email: string, password: string) =>
  api<{ token: string; user: User }>("/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });

export const signup = (input: {
  email: string;
  password: string;
  full_name: string;
  university?: string;
  roll_number?: string;
}) =>
  api<{ token: string; user: User }>("/auth/signup", {
    method: "POST",
    body: input,
    auth: false,
  });

export const logout = () => api<void>("/auth/logout", { method: "POST" });

export const getMe = () => api<User>("/auth/me");

export const updatePreferences = (preferred_language: string) =>
  api<User>("/auth/me/preferences", {
    method: "PATCH",
    body: { preferred_language },
  });

// --- admin (admin-001 .. admin-006) -----------------------------------
//
// Shapes mirror `_course_out`, `_material_out` and the audit-log row in
// backend/app/routers/admin.py. Every one of these is admin-only server-side:
// a non-admin token gets 403, which is the guard, not the UI.

export type Department = { id: number; name: string };

export type Course = {
  id: number;
  code: string;
  title: string;
  department_id: number | null;
  prerequisite_courses: { id: number; code: string; title: string }[];
  semester: number | null;
  admission_batches: number[];
  /** admin-010: the cohorts that take this subject (real Batch ids). */
  batch_ids: number[];
  term_start: string | null;
  term_end: string | null;
};

/** `kind` is the closed list the backend accepts -- see admin-007. */
export type MaterialKind = "textbook" | "syllabus" | "assignment" | "reference";

export type Material = {
  id: number;
  course_id: number;
  title: string;
  kind: MaterialKind;
  version: number;
  status: "active" | "archived";
  page_count: number | null;
  uploaded_by: string | null;
  uploaded_at: string | null;
  ingest_status: string;
  chunk_count: number;
};

export type AuditRow = {
  id: number;
  actor_email: string;
  action: string;
  target: string;
  at: string;
  detail: Record<string, unknown>;
  /** admin-004: a plain sentence. Render this, keep the rest behind details. */
  summary: string;
};

export const listDepartments = () =>
  api<{ items: Department[] }>("/admin/departments");

export const listCourses = () => api<{ items: Course[] }>("/admin/courses");

export const getCourse = (courseId: number) =>
  api<Course>(`/admin/courses/${courseId}`);

export const listMaterials = (courseId: number, includeArchived = false) =>
  api<{ items: Material[] }>(
    `/admin/courses/${courseId}/materials?include_archived=${includeArchived}`,
  );

/** multipart. `chapter_map` is optional and omitted when empty. */
export const uploadMaterial = (
  courseId: number,
  file: File,
  kind: MaterialKind,
  title: string,
  chapterMap?: string,
) => {
  const form = new FormData();
  form.append("file", file);
  form.append("kind", kind);
  form.append("title", title);
  if (chapterMap) form.append("chapter_map", chapterMap);
  return upload<Material>(`/admin/courses/${courseId}/materials`, form);
};

export const archiveMaterial = (materialId: number) =>
  api<Material>(`/admin/materials/${materialId}/archive`, { method: "POST" });

/**
 * admin-006. Guarded server-side: `409 mid_term` when the material is already
 * ingested and the course is inside its teaching window. Callers must surface
 * that message rather than swallowing it -- it tells the admin to archive.
 */
export const deleteMaterial = (materialId: number) =>
  api<void>(`/admin/materials/${materialId}`, { method: "DELETE" });

export const listAuditLog = (opts: {
  limit?: number;
  offset?: number;
  actor?: string;
  action?: string;
  includeSystem?: boolean;
} = {}) => {
  const q = new URLSearchParams();
  q.set("limit", String(opts.limit ?? 50));
  q.set("offset", String(opts.offset ?? 0));
  if (opts.actor) q.set("actor", opts.actor);
  if (opts.action) q.set("action", opts.action);
  if (opts.includeSystem) q.set("include_system", "true");
  return api<{ items: AuditRow[]; total: number }>(`/admin/audit-log?${q}`);
};

/**
 * admin-011. The bell. Both sources are audit rows, so a NotificationRow is
 * an AuditRow plus three derived fields -- render `summary` with whatever the
 * audit log already uses and switch icons on `kind`, never on the sentence.
 */
export type NotificationRow = AuditRow & {
  kind: "audit" | "teacher_first_login";
  /** Newer than your last read AND not something you did yourself. */
  unread: boolean;
  by_you: boolean;
};

export const listNotifications = (limit = 20, offset = 0) =>
  api<{
    items: NotificationRow[];
    /** Counted over the whole table, not this page, and never your own acts. */
    unread: number;
    seen_at: string | null;
    total: number;
  }>(`/admin/notifications?limit=${limit}&offset=${offset}`);

export const markNotificationsRead = () =>
  api<{ seen_at: string; unread: number }>("/admin/notifications/read", {
    method: "POST",
  });

// --- admin: course management (admin-008 UI over admin-002/admin-005) ---

/** POST /admin/courses -- prerequisite_course_ids is required by the contract,
 *  send [] for a standalone course. */
export const createCourse = (input: {
  code: string;
  title: string;
  department_id: number | null;
  prerequisite_course_ids?: number[];
}) =>
  api<Course>("/admin/courses", {
    method: "POST",
    body: { prerequisite_course_ids: [], ...input },
  });

export const createDepartment = (name: string) =>
  api<Department>("/admin/departments", { method: "POST", body: { name } });

/**
 * PUT /admin/courses/{id}/term (admin-005). Send ONLY the fields being
 * changed; to clear one, send it explicitly as null (or [] for batches).
 * The window is load-bearing: admin-006's delete guard reads it, which is
 * why the UI states it plainly rather than burying it in an "advanced" tab.
 */
export const updateCourseTerm = (
  courseId: number,
  input: {
    semester?: number | null;
    admission_batches?: number[] | null;
    term_start?: string | null;
    term_end?: string | null;
  },
) => api<Course>(`/admin/courses/${courseId}/term`, { method: "PUT", body: input });

// --- student surface (student-001 .. 009, rag-003/004) ----------------------

export type CourseSummary = {
  course: { code: string; title: string };
  books: { title: string; kind: string }[];
  topics: { id: number; name: string }[];
};

export type Gap = {
  id: number;
  concept: string;
  prerequisite_course: string;
  detected_from: "diagnostic" | "syllabus_upload" | "practice";
  status: "open" | "improving" | "closed";
  suggested_prompts: string[];
  latest_practice_set_id: number | null;
};

export type MasteryTopic = {
  topic_id: number;
  topic: string;
  concepts: { id: number; name: string; state: "solid" | "shaky" | "untested" }[];
};

export type Assignment = {
  id: number;
  title: string;
  body: string;
  assigned_at: string;
  citations: Citation[];
};

export type PracticeItemDto = {
  id: number;
  prompt: string;
  kind: string;
  options: string[] | null;
  gap_id?: number;
  your_answer?: string | null;
  correct?: boolean | null;
  diagnosis?: PracticeDiagnosis | null;
};

export type PracticeDiagnosis = {
  id: number;
  misconception_id: number;
  label: string;
  question: string;
  confirmed?: boolean | null;
};

export type AnswerResult = {
  correct: boolean;
  correct_answer: string;
  explanation: string;
  citations: Citation[];
  diagnosis: PracticeDiagnosis | null;
};

export type PracticeSet = {
  practice_set_id: number;
  concept: string;
  source: string;
  items: PracticeItemDto[];
};

export type DiagnosticDto = {
  diagnostic_id: number;
  submitted_at: string | null;
  items: (PracticeItemDto & { concept?: string })[];
};

export const getCourseSummary = () => api<CourseSummary>("/student/course-summary");
export const getGaps = () => api<{ items: Gap[] }>("/student/gaps");
export const getGapLesson = (gapId: number, language = "en") =>
  api<TutorResponse>(`/student/gaps/${gapId}/lesson?language=${language}`);
export const getMastery = () => api<{ items: MasteryTopic[] }>("/student/mastery");
export const getAssignments = () => api<{ items: Assignment[] }>("/student/assignments");
export const getDiagnostic = () => api<DiagnosticDto>("/student/diagnostic");
export const submitDiagnostic = (diagnosticId: number, answers: { item_id: number; answer: string }[]) =>
  api<{ gaps: Gap[]; message: string }>(`/student/diagnostic/${diagnosticId}/submit`, {
    method: "POST",
    body: { answers },
  });
export const generatePractice = (gapId: number, count = 3) =>
  api<PracticeSet>("/student/practice/generate", { method: "POST", body: { gap_id: gapId, count } });
export const getPracticeSet = (setId: number) => api<PracticeSet>(`/student/practice/${setId}`);
export const answerPractice = (setId: number, itemId: number, answer: string) =>
  api<AnswerResult>(`/student/practice/${setId}/answer`, {
    method: "POST",
    body: { item_id: itemId, answer },
  });
export const confirmMisconception = (diagnosisId: number, confirmed: boolean) =>
  api<void>(`/student/misconception-diagnosis/${diagnosisId}/confirm`, {
    method: "POST",
    body: { confirmed },
  });
export const askTutor = (question: string, language = "en") =>
  api<TutorResponse>("/tutor/ask", { method: "POST", body: { question, language } });

/** tutor-002 — the signed-in student's own transcript, oldest first. */
export type TutorHistoryItem =
  | { id: number; role: "student"; text: string; response: null; created_at: string }
  | { id: number; role: "tutor"; text: null; response: TutorResponse; created_at: string };

export const getTutorHistory = (limit = 100) =>
  api<{ items: TutorHistoryItem[] }>(`/tutor/history?limit=${limit}`).then((r) => r.items);

// --- session cache (perf-002) ---------------------------------------------
//
// Why: the student dashboard refetches on every view switch, and each view is
// 1-4 sequential calls over a remote-DB link at ~137-320ms a round trip
// (perf-001 measured this) — the 3s the views felt. The cache below is
// stale-while-revalidate: a warm key resolves from memory (instant switch),
// an expired one STILL paints from memory while a refresh runs in the
// background and re-setStates when it lands. React StrictMode's double-mount
// is deduped by the in-flight map.
//
// Correctness rests on the caller invalidating on mutation — the keys below
// are paired with their invalidations at every mutation site in the app:
//   diagnostic submit  -> "diagnostic", "gaps", "mastery"
//   practice answer    -> `practice:<id>`, "gaps", "mastery"
//   misconception confirm -> "gaps", "mastery"
//   tutor ask          -> "tutor-history"
//   preferences PATCH  -> "me"
// login and logout clear the whole map: the cache must never outlive the
// token it was fetched with.

type CacheEntry = { at: number; data: unknown };
const sessionCache = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<unknown>>();

function revalidate<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
  const existing = inflight.get(key) as Promise<T> | undefined;
  if (existing) return existing;
  const p = fetcher()
    .then((data) => {
      sessionCache.set(key, { at: Date.now(), data });
      return data;
    })
    .finally(() => {
      if (inflight.get(key) === p) inflight.delete(key);
    });
  inflight.set(key, p);
  return p;
}

/** Read-through with stale-while-revalidate. Views call this in place of the
 *  bare getter inside their existing useEffect — the returned promise
 *  resolves instantly from memory whenever any data is cached. */
export async function cached<T>(key: string, fetcher: () => Promise<T>, ttlMs = 60_000): Promise<T> {
  const hit = sessionCache.get(key);
  if (hit && Date.now() - hit.at < ttlMs) return hit.data as T;
  if (hit) {
    // Stale but paintable: refresh silently; a failure here must not turn a
    // working screen into an error screen.
    revalidate(key, fetcher).catch(() => {});
    return hit.data as T;
  }
  return revalidate(key, fetcher);
}

export function invalidateCache(...keys: string[]) {
  for (const k of keys) sessionCache.delete(k);
}

export function clearSessionCache() {
  sessionCache.clear();
  inflight.clear();
}

// --- teacher endpoints (frontend-003) --------------------------------------

export type HeatmapItem = {
  misconception_id: number;
  label: string;
  confirmed_count: number;
  share: number;
  problem_type: string;
};

export type Heatmap = {
  topic: string;
  class_size: number;
  updated_at: string;
  items: HeatmapItem[];
};

export type UncertaintyFlagDto = {
  id: number;
  question: string;
  alignment_percent: number;
  reason: string;
  topic_id: number | null;
  occurred_at: string;
  status: string;
};

export type GapMapItem = {
  concept: string;
  prerequisite_course: string;
  students_missing: number;
  share: number;
};

export type ReteachUnitDto = {
  id: number;
  misconception_id: number | null;
  concept_id: number | null;
  target: string;
  label: string;
  title: string;
  body: string;
  status: string;
  approved_by: number | null;
};

/** course_id is deliberately not passed: the teacher router scopes to the
 *  signed-in teacher's own course, exactly like /tutor does for students. */
export const getHeatmap = () =>
  api<Heatmap>("/teacher/misconceptions/heatmap").then((r) => r);

export const getUncertaintyFlags = (status = "open") =>
  api<{ items: UncertaintyFlagDto[] }>(`/teacher/uncertainty-flags?status=${status}`).then(
    (r) => r.items,
  );

export const resolveUncertaintyFlag = (id: number, note?: string) =>
  api<void>(`/teacher/uncertainty-flags/${id}/resolve`, {
    method: "POST",
    body: note ? { note } : {},
  });

export const getGapMap = () =>
  api<{ items: GapMapItem[] }>("/teacher/gap-map").then((r) => r.items);

export const getReteachUnits = (status?: string) =>
  api<{ items: ReteachUnitDto[] }>(
    `/teacher/reteach${status ? `?status=${status}` : ""}`,
  ).then((r) => r.items);

export const approveReteachUnit = (id: number) =>
  api<ReteachUnitDto>(`/teacher/reteach/${id}/approve`, { method: "POST" });

/** teacher-008. Drafts the top 3 of each ranking in one press. Idempotent --
 *  safe to press during a rehearsal. First press on cold cache takes ~a minute
 *  of model calls; the disk cache makes every later press free. */
export const suggestTopReteach = () =>
  api<{ drafted: ReteachUnitDto[]; skipped: { reason: string }[] }>(
    "/teacher/reteach/suggest-top",
    { method: "POST", body: {} },
  );

// --- teacher panels, second pass (frontend-004) ----------------------------

export type ReasoningExample = { given_answer: string; reasoning: string };

export type ReasoningPathItem = {
  misconception_id: number;
  label: string;
  confirmed_count: number;
  /** Null when no confirmed diagnosis carries a stored answer to show. */
  example: ReasoningExample | null;
};

/** teacher-002. The reasoning paths behind ONE kind of problem; the
 *  problem_type values to offer come from the heatmap's items. */
export const getReasoningPaths = (problemType: string) =>
  api<{ problem_type: string; items: ReasoningPathItem[] }>(
    `/teacher/problems/${encodeURIComponent(problemType)}/reasoning-paths`,
  ).then((r) => r.items);

export type BeforeAfterWindow = {
  window: string;
  confirmed_count: number;
  share: number;
  attempts_in_window?: number;
  measured?: boolean;
};

export type BeforeAfter = {
  misconception_id: number;
  label: string;
  before: BeforeAfterWindow;
  /** Null until a reteach was approved -- deliberately not zero. */
  after: BeforeAfterWindow | null;
  reteach_at: string | null;
  /** Null until `after.measured` -- zero evidence is not zero occurrences. */
  delta_share: number | null;
  note?: string;
};

/** teacher-005. The one panel that can say the reteach did not work. */
export const getBeforeAfter = (misconceptionId: number) =>
  api<BeforeAfter>(`/teacher/misconceptions/${misconceptionId}/before-after`);

export type VerificationItem = {
  id: number;
  source_url: string;
  title: string;
  excerpt: string;
  found_for_gap: string;
  status: string;
  reject_reason: string | null;
  found_at: string | null;
};

/** teacher-007. Seeded by design -- no live web search in this build. A
 *  pending item is unreachable from every student endpoint; that is the
 *  property that makes "curriculum-aligned" mean anything. */
export const getVerificationQueue = (status = "pending") =>
  api<{ items: VerificationItem[] }>(`/teacher/verification-queue?status=${status}`).then(
    (r) => r.items,
  );

export const approveVerificationItem = (id: number) =>
  api<VerificationItem>(`/teacher/verification-queue/${id}/approve`, { method: "POST" });

export const rejectVerificationItem = (id: number, reason?: string) =>
  api<VerificationItem>(`/teacher/verification-queue/${id}/reject`, {
    method: "POST",
    body: reason ? { reason } : {},
  });

// --- admin batches / teachers / overview (admin-009) ------------------------

export const getOverview = () =>
  api<OverviewDto>("/admin/overview");

export const getBatches = () =>
  api<{ items: BatchDto[] }>("/admin/batches").then((r) => r.items);

export const createBatch = (major: string, department_id: number, start_year: number) =>
  api<BatchDto>("/admin/batches", { method: "POST", body: { major, department_id, start_year } });

export const uploadBatchCurriculum = (batchId: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return upload<BatchDto>(`/admin/batches/${batchId}/curriculum`, form);
};

export const reuseBatchCurriculum = (batchId: number, fromBatchId: number) =>
  api<BatchDto>(`/admin/batches/${batchId}/curriculum/reuse`, {
    method: "POST",
    body: { from_batch_id: fromBatchId },
  });

export const getCourseTeachers = (courseId: number) =>
  api<{ items: AssignedTeacher[] }>(`/admin/courses/${courseId}/teachers`).then(
    (r) => r.items,
  );

/** The password is returned ONCE, only when a new account was issued. */
export const addCourseTeacher = (courseId: number, email: string, fullName?: string) =>
  api<{ teacher: AssignedTeacher; password: string | null; already_assigned: boolean }>(
    `/admin/courses/${courseId}/teachers`,
    { method: "POST", body: { email, full_name: fullName } },
  );

export const removeCourseTeacher = (courseId: number, userId: number) =>
  api<void>(`/admin/courses/${courseId}/teachers/${userId}`, { method: "DELETE" });

// --- subjects in a batch (admin-010) ---------------------------------------

export const getBatchCourses = (batchId: number) =>
  api<{ items: BatchCourse[] }>(`/admin/batches/${batchId}/courses`).then((r) => r.items);

/** Link an existing subject, or create one in the batch's department. */
export const addBatchCourse = (
  batchId: number,
  body: { course_id: number } | { code: string; title: string; semester?: number },
) => api<BatchCourse>(`/admin/batches/${batchId}/courses`, { method: "POST", body });

export const removeBatchCourse = (batchId: number, courseId: number) =>
  api<void>(`/admin/batches/${batchId}/courses/${courseId}`, { method: "DELETE" });

// --- enrolment + subject switching (student-010, teacher-009) --------------

export type MySubject = {
  id: number;
  code: string;
  title: string;
  semester: number | null;
  is_current: boolean;
};

export type TeacherSubject = MySubject & {
  batches: {
    id: number;
    major: string;
    department: string;
    start_year: number;
    end_year: number;
  }[];
};

/** The cohorts a student may join. No roll-list check by decision (auth-004). */
export const getEnrollableBatches = () =>
  api<{ items: BatchDto[] }>("/student/batches").then((r) => r.items);

/** Join a cohort. Without a course_id the earliest-semester subject is used. */
export const enroll = (batch_id: number, course_id?: number) =>
  api<User>("/student/enroll", { method: "POST", body: { batch_id, course_id } });

export const getMySubjects = () =>
  api<{ batch: BatchDto | null; items: MySubject[] }>("/student/subjects");

/** Moves the WHOLE student surface: gaps, mastery, practice, tutor. */
export const setActiveSubject = (course_id: number) =>
  api<User>("/student/active-subject", { method: "PATCH", body: { course_id } });

export const getTeacherSubjects = () =>
  api<{ items: TeacherSubject[] }>("/teacher/subjects").then((r) => r.items);

/** Moves every teacher panel at once -- they all scope by this one field. */
export const setTeacherActiveSubject = (course_id: number) =>
  api<User>("/teacher/active-subject", { method: "PATCH", body: { course_id } });

// --- the material library (teacher-010) ------------------------------------

export type TeacherMaterial = {
  id: number;
  course_id: number;
  course_code: string | null;
  course_title: string | null;
  title: string;
  kind: string;
  page_count: number;
  chunk_count: number;
  ingest_status: string;
  uploaded_at: string | null;
  /** false when the row outlived the file on disk */
  has_file: boolean;
};

export const getTeacherMaterials = (courseId?: number) =>
  api<{ items: TeacherMaterial[] }>(
    `/teacher/materials${courseId ? `?course_id=${courseId}` : ""}`,
  ).then((r) => r.items);

/**
 * A plain <a href> cannot send an Authorization header, so the token rides
 * as a query parameter for this one route. It is the same opaque session
 * token the header would carry -- no new authority -- and it keeps View and
 * Save as ordinary links the browser can open and download natively.
 */
export const materialFileUrl = (materialId: number, download = false) => {
  const t = getToken();
  const qs = new URLSearchParams();
  if (download) qs.set("download", "1");
  if (t) qs.set("token", t);
  return `${BASE}/teacher/materials/${materialId}/file?${qs.toString()}`;
};
