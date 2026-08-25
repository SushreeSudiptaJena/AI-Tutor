// USE_MOCK lets auth pages be built/demoed before the backend or tunnel is
// reachable (handbook section 9.4). Flip to false once your VITE_API_BASE
// points at a live backend and auth-001 is verified against it.
export const USE_MOCK = false;

import type { User, Role } from "./api";

const MOCK_DELAY = 500;

export async function mockLogin(email: string, _password: string): Promise<{ token: string; user: User }> {
  await new Promise((r) => setTimeout(r, MOCK_DELAY));
  return {
    token: "mock-token",
    user: { id: 1, email, full_name: "Test User", role: "student", preferred_language: "en" },
  };
}

export async function mockSignup(input: {
  email: string;
  password: string;
  full_name: string;
  role: Role;
}): Promise<{ token: string; user: User }> {
  await new Promise((r) => setTimeout(r, MOCK_DELAY));
  return {
    token: "mock-token",
    user: { id: 1, email: input.email, full_name: input.full_name, role: input.role, preferred_language: "en" },
  };
}