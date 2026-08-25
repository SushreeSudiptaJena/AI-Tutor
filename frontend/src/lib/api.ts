/**
 * Every fetch in the app goes through this file. Nowhere else.
 *
 * Shapes here mirror docs/api-contract.md -- if that file changes, change this
 * one in the same commit.
 */

const BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "ai_tutor_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t: string) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

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

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  course_id?: number;
  preferred_language: string;
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
    }
  | {
      outcome: "insufficient_evidence";
      language: string;
      body: string;
      citations: [];
      evidence: EvidenceReport;
      uncertainty_flag_id: number;
    }
  | {
      outcome: "graded_work_refused";
      language: string;
      body: string;
      hints: string[];
      citations: Citation[];
      matched_assignment: { material_id: number; title: string };
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
  role: Role;
  course_id?: number;
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
