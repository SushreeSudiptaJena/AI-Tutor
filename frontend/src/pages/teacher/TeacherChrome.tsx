import { ReactNode, useEffect, useState } from "react";
import {
  cached,
  clearSessionCache,
  getMe,
  getTeacherSubjects,
  getUncertaintyFlags,
  setTeacherActiveSubject,
  type TeacherSubject,
  type UncertaintyFlagDto,
} from "@/lib/api";

/**
 * The sidebar + header shared by the teacher screens (111d770's Stitch
 * conversion), extracted so the live-wired panels (frontend-003) don't each
 * carry a 3kB copy of it. Navigation still works exactly as shipped: plain
 * <a data-path> links, with the click handled by TeacherDashboard's single
 * delegated listener.
 *
 * The header name is the real signed-in teacher (/auth/me), not "Dr. Sarah
 * Ascent" -- the screens arrived with a placeholder persona baked in.
 */

// Students, Attendance and Assignments are gone: they were static mockups
// with no endpoint behind them, and this build deliberately stores no
// attendance or per-student roster (see the absences at the top of
// models.py). Lesson Plans is the material library (teacher-010).
const NAV_TOP: [string, string, string][] = [
  ["dashboard", "dashboard", "Dashboard"],
  ["my-classes", "school", "My Classes"],
  ["lesson-plans", "auto_stories", "Lesson Plans"],
];

const NAV_INSIGHTS: [string, string, string][] = [
  ["misconception-heatmap", "thermostat", "Heatmap"],
  ["reasoning-path-breakdown", "route", "Reasoning Paths"],
  ["gap-map", "map", "Gap Map"],
  ["uncertainty-flags", "warning", "Uncertainty"],
  ["tracking", "analytics", "Tracking"],
  ["suggested-reteach", "psychology", "Reteach"],
  ["content-verification", "verified", "Verification"],
];

function itemClasses(active: boolean): string {
  return active
    ? "font-mono text-[13px] tracking-wide flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-on-primary font-semibold border-l-4 border-secondary"
    : "font-mono text-[13px] tracking-wide flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-on-primary transition-all gap-3 text-on-primary";
}

export default function TeacherChrome({
  active,
  children,
}: {
  active: string;
  children: ReactNode;
}) {
  const [name, setName] = useState<string>("…");
  // teacher-009: every panel scopes by the signed-in teacher's active
  // subject, so this one control moves the entire console.
  const [subjects, setSubjects] = useState<TeacherSubject[]>([]);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    let alive = true;
    cached("me", getMe)
      .then((me) => alive && setName(me.full_name))
      .catch(() => alive && setName("Teacher"));
    cached("teacher-subjects", getTeacherSubjects)
      .then((r) => alive && setSubjects(r))
      .catch(() => alive && setSubjects([]));
    return () => {
      alive = false;
    };
  }, []);

  async function switchTo(courseId: number) {
    setSwitching(true);
    try {
      await setTeacherActiveSubject(courseId);
      // Nothing cached belongs to the new subject; reload rather than trying
      // to invalidate each panel's key by hand.
      clearSessionCache();
      window.location.reload();
    } catch {
      setSwitching(false);
    }
  }

  const current = subjects.find((s) => s.is_current);

  // The bell was decorative. It now opens what a teacher would actually
  // want behind it: the open uncertainty flags, with a way into the panel.
  const [bellOpen, setBellOpen] = useState(false);
  const [flags, setFlags] = useState<UncertaintyFlagDto[]>([]);
  useEffect(() => {
    let alive = true;
    cached("flags-open", () => getUncertaintyFlags("open"))
      .then((r) => alive && setFlags(r))
      .catch(() => alive && setFlags([]));
    return () => {
      alive = false;
    };
  }, []);

  const link = ([path, icon, label]: [string, string, string]) => (
    <a
      key={path}
      aria-current={path === active ? "page" : undefined}
      className={itemClasses(path === active)}
      data-path={path}
      href="#"
    >
      <span className={`material-symbols-outlined${path === active ? " text-secondary" : ""}`}>
        {icon}
      </span>
      {label}
    </a>
  );

  return (
    <>
      <aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5">
        <div className="px-card-padding py-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45">
            <span className="material-symbols-outlined text-on-secondary -rotate-45">landscape</span>
          </div>
          <span className="font-headline-lg text-headline-lg text-on-primary tracking-tight">ASCENT</span>
        </div>
        <nav className="flex-1 px-4 flex flex-col gap-1">
          {NAV_TOP.map(link)}
          <div className="my-4 border-t border-on-primary/10"></div>
          <div className="px-4 py-2 text-label-sm font-label-sm text-on-primary uppercase tracking-widest">
            AI Insights
          </div>
          {NAV_INSIGHTS.map(link)}
          <div className="mt-auto mb-6 flex flex-col gap-1">
            <a
              className="flex items-center px-4 py-3 rounded-lg text-on-primary hover:bg-surface/5 hover:text-on-primary transition-all gap-3"
              data-path="settings"
              href="#"
            >
              <span className="material-symbols-outlined">settings</span>Settings
            </a>
          </div>
        </nav>
      </aside>
      <div className="pl-sidebar-width min-h-screen bg-paper">
        <header className="fixed top-0 left-sidebar-width right-0 h-20 bg-ink/95 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm">
          {/* teacher-009: the subject this console is showing. Replaces a
              decorative search box that had no endpoint behind it. */}
          <div className="flex-1 max-w-[36rem] flex items-center gap-3">
            {subjects.length === 0 ? (
              <span className="font-label-sm text-label-sm text-on-primary/70">
                No subjects assigned yet — your admin assigns them.
              </span>
            ) : (
              <>
                <span className="material-symbols-outlined text-on-primary">menu_book</span>
                <select
                  value={current?.id ?? ""}
                  disabled={switching}
                  onChange={(e) => switchTo(Number(e.target.value))}
                  aria-label="Subject this console is showing"
                  className="bg-[#FFFFFF]/10 border border-on-primary/20 rounded-full px-4 py-2 text-on-primary font-body-md outline-none focus:border-secondary disabled:opacity-50"
                >
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id} className="text-ink">
                      {s.code} — {s.title}
                      {s.batches.length
                        ? ` (${s.batches
                            .map((b) => `${b.major.toUpperCase()} ${b.start_year}`)
                            .join(", ")})`
                        : ""}
                    </option>
                  ))}
                </select>
                {current?.batches?.length ? (
                  <span className="font-label-sm text-label-sm text-on-primary/70 hidden lg:inline">
                    {current.batches.length} cohort{current.batches.length === 1 ? "" : "s"}
                  </span>
                ) : null}
              </>
            )}
          </div>
          <div className="flex items-center gap-6">
            <div className="relative">
              <button
                onClick={() => setBellOpen((v) => !v)}
                aria-label={`Notifications (${flags.length} open uncertainty flags)`}
                aria-expanded={bellOpen}
                className="relative text-on-primary hover:opacity-80 transition-opacity"
              >
                <span className="material-symbols-outlined">notifications</span>
                {flags.length > 0 && (
                  <span className="absolute -top-1 -right-1 min-w-4 h-4 px-1 bg-orange text-on-primary rounded-full font-label-sm text-[10px] flex items-center justify-center">
                    {flags.length}
                  </span>
                )}
              </button>

              {bellOpen && (
                <div className="absolute right-0 mt-3 w-[22rem] bg-card text-ink rounded-xl border border-outline-variant shadow-[0_10px_22px_-14px_rgba(43,41,38,0.28)] p-4 z-50">
                  <p className="font-label-sm text-label-sm uppercase tracking-widest text-ink-faint mb-3">
                    Open uncertainty flags
                  </p>
                  {flags.length === 0 ? (
                    <p className="font-body-md text-body-md text-ink-soft">
                      Nothing outstanding — everything the class asked was grounded in the
                      material.
                    </p>
                  ) : (
                    <>
                      <ul className="space-y-2 max-h-[16rem] overflow-y-auto">
                        {flags.slice(0, 5).map((f) => (
                          <li key={f.id} className="font-body-md text-body-md line-clamp-2">
                            {f.question}
                          </li>
                        ))}
                      </ul>
                      <a
                        href="#"
                        data-path="uncertainty-flags"
                        onClick={() => setBellOpen(false)}
                        className="mt-3 inline-block font-label-md text-label-md text-orange hover:underline"
                      >
                        See all {flags.length} →
                      </a>
                    </>
                  )}
                </div>
              )}
            </div>
            {/* Profile lives behind the avatar; Settings stays in the
                sidebar. They were one screen before. */}
            <a
              href="#"
              data-path="profile"
              aria-label="Open your profile"
              className="flex items-center gap-3 pl-6 border-l border-on-primary/20 hover:opacity-80 transition-opacity"
            >
              <div className="text-right hidden sm:block">
                <div className="text-body-md font-semibold text-on-primary">{name}</div>
                <div className="text-label-sm text-on-primary">Educator</div>
              </div>
              <div className="w-10 h-10 rounded-full bg-orange flex items-center justify-center shadow-lg">
                <span className="material-symbols-outlined text-on-primary text-[22px]">person</span>
              </div>
            </a>
          </div>
        </header>
        <main className="pt-20 p-margin-desktop bg-paper text-ink">
          <div className="flex flex-col w-full relative min-h-[800px] font-body-md text-on-primary p-6 gap-12">
            {children}
          </div>
        </main>
      </div>
    </>
  );
}
