/**
 * Teacher profile -- reached from the avatar, separate from Settings.
 *
 * Profile is about the person (who you are, what you teach, signing out);
 * Settings is about the console's behaviour. They were one screen before.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import TeacherChrome from "./TeacherChrome";
import {
  cached,
  clearToken,
  getMe,
  getTeacherSubjects,
  logout,
  type TeacherSubject,
  type User,
} from "@/lib/api";

export default function TeacherProfile() {
  const navigate = useNavigate();
  const [me, setMe] = useState<User | null>(null);
  const [subjects, setSubjects] = useState<TeacherSubject[]>([]);

  useEffect(() => {
    let alive = true;
    cached("me", getMe)
      .then((u) => alive && setMe(u))
      .catch(() => {});
    cached("teacher-subjects", getTeacherSubjects)
      .then((r) => alive && setSubjects(r))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  async function signOut() {
    try {
      await logout();
    } catch {
      // the token is unusable for anything real; drop it regardless
    } finally {
      clearToken();
      navigate("/login", { replace: true });
    }
  }

  const facts: [string, string][] = [
    ["Name", me?.full_name ?? "…"],
    ["Email", me?.email ?? "…"],
    ["Role", "Educator"],
    ["Subjects assigned", String(subjects.length)],
  ];

  return (
    <TeacherChrome active="profile">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-orange">person</span>
            Your account
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">Profile</h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            Your account is issued by your department admin — including your password. Console
            preferences live under Settings.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        <section className="bg-card p-8 rounded-2xl border border-outline-variant shadow-[0_6px_14px_-10px_rgba(43,41,38,0.24)]">
          <h2 className="font-title-md text-title-md text-ink mb-6 pb-4 border-b border-ink/10">
            Details
          </h2>
          <dl className="space-y-4">
            {facts.map(([k, v]) => (
              <div key={k} className="flex items-baseline justify-between gap-4">
                <dt className="font-label-sm text-label-sm uppercase tracking-widest text-ink-faint">
                  {k}
                </dt>
                <dd className="font-body-md text-body-md text-ink text-right">{v}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="bg-card p-8 rounded-2xl border border-outline-variant shadow-[0_6px_14px_-10px_rgba(43,41,38,0.24)] flex flex-col">
          <h2 className="font-title-md text-title-md text-ink mb-6 pb-4 border-b border-ink/10">
            What you teach
          </h2>
          {subjects.length === 0 ? (
            <p className="font-body-md text-body-md text-ink-soft">
              No subjects assigned yet.
            </p>
          ) : (
            <ul className="space-y-3">
              {subjects.map((s) => (
                <li key={s.id} className="flex items-baseline justify-between gap-4">
                  <span className="font-body-md text-body-md text-ink">
                    <span className="text-orange">{s.code}</span> · {s.title}
                  </span>
                  <span className="font-label-sm text-label-sm text-ink-faint shrink-0">
                    {s.batches.length} cohort{s.batches.length === 1 ? "" : "s"}
                  </span>
                </li>
              ))}
            </ul>
          )}

          <button onClick={signOut} className="btn-ghost mt-auto self-start pt-2">
            Sign out
          </button>
        </section>
      </div>
    </TeacherChrome>
  );
}
