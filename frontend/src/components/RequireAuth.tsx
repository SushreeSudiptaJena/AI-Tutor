import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { getMe, clearToken, getToken, ApiError } from "@/lib/api";
import type { Role, User } from "@/lib/api";

/**
 * Route guard. Two jobs, and the second is the one that matters.
 *
 * 1. No token at all -> straight to /login, no network call.
 * 2. A token that the SERVER rejects -> also /login, token cleared.
 *
 * (2) is why this calls `GET /auth/me` instead of just checking localStorage.
 * A token is an opaque UUID in a `sessions` table -- it can be invalidated
 * server-side by logout, or simply be stale from a previous demo run, and the
 * client has no way to know by looking at it. Trusting localStorage alone
 * produces the worst failure on stage: the dashboard renders, then every panel
 * inside it fails with a 401 and the screen fills with error states.
 *
 * `role` narrows further: an authenticated student who types /admin is sent
 * home rather than shown a shell whose every request will 403.
 */
export default function RequireAuth({
  children,
  role,
}: {
  children: JSX.Element;
  role?: Role;
}) {
  const location = useLocation();
  const [state, setState] = useState<"checking" | "ok" | "denied">(
    getToken() ? "checking" : "denied",
  );
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!getToken()) return;
    let alive = true;
    getMe()
      .then((u) => {
        if (!alive) return;
        setUser(u);
        setState("ok");
      })
      .catch((err) => {
        if (!alive) return;
        // 401 means the session is gone; anything else (tunnel down, CORS)
        // is not the user's fault, but there is no safe way to render a
        // guarded page without knowing who they are, so both deny.
        if (err instanceof ApiError && err.status === 401) clearToken();
        setState("denied");
      });
    return () => {
      alive = false;
    };
  }, []);

  if (state === "checking") {
    return (
      <div className="min-h-screen flex items-center justify-center text-on-surface-variant">
        Checking your session…
      </div>
    );
  }

  if (state === "denied") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (role && user?.role !== role) {
    // Send them to their OWN surface, not to a login screen: they are signed
    // in, and asking a logged-in teacher to log in again reads as "your
    // session broke". A student who types /admin still lands somewhere they
    // can use.
    const home =
      user?.role === "admin"
        ? "/admin"
        : user?.role === "teacher"
          ? "/teacher"
          : user?.course_id
            ? "/dashboard"
            : "/onboarding/course";
    return <Navigate to={home} replace state={{ wrongRole: true }} />;
  }

  return children;
}
