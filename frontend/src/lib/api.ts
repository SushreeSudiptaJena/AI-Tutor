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
