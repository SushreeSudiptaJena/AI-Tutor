import { ReactNode, useEffect, useState } from "react";
import { cached, getMe } from "@/lib/api";

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

const NAV_TOP: [string, string, string][] = [
  ["dashboard", "dashboard", "Dashboard"],
  ["my-classes", "school", "My Classes"],
  ["students", "group", "Students"],
  ["attendance", "how_to_reg", "Attendance"],
  ["lesson-plans", "auto_stories", "Lesson Plans"],
  ["assignments", "assignment", "Assignments"],
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
    ? "flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-[#FFFFFF] font-semibold border-l-4 border-secondary"
    : "flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]";
}

export default function TeacherChrome({
  active,
  children,
}: {
  active: string;
  children: ReactNode;
}) {
  const [name, setName] = useState<string>("…");

  useEffect(() => {
    let alive = true;
    cached("me", getMe)
      .then((me) => alive && setName(me.full_name))
      .catch(() => alive && setName("Teacher"));
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
          <span className="font-headline-lg text-headline-lg text-[#FFFFFF] tracking-tight">ASCENT</span>
        </div>
        <nav className="flex-1 px-4 flex flex-col gap-1">
          {NAV_TOP.map(link)}
          <div className="my-4 border-t border-[#FFFFFF]/10"></div>
          <div className="px-4 py-2 text-label-sm font-label-sm text-[#FFFFFF] uppercase tracking-widest">
            AI Insights
          </div>
          {NAV_INSIGHTS.map(link)}
          <div className="mt-auto mb-6 flex flex-col gap-1">
            <a
              className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3"
              data-path="settings"
              href="#"
            >
              <span className="material-symbols-outlined">settings</span>Settings
            </a>
          </div>
        </nav>
      </aside>
      <div className="pl-sidebar-width min-h-screen bg-inverse-surface">
        <header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm">
          <div className="flex-1 max-w-xl bg-[#FFFFFF]/10 rounded-full px-6 py-2 flex items-center gap-3 border border-[#FFFFFF]/20 focus-within:border-secondary transition-colors">
            <span className="material-symbols-outlined text-[#FFFFFF]">search</span>
            <input
              className="bg-transparent border-none outline-none text-[#FFFFFF] w-full font-body-md placeholder-[#FFFFFF]"
              placeholder="Search the mountain path..."
              type="text"
            />
          </div>
          <div className="flex items-center gap-6">
            <button className="relative text-[#FFFFFF] hover:text-[#F5F5F5] transition-colors">
              <span className="material-symbols-outlined">notifications</span>
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div>
            </button>
            <div className="flex items-center gap-3 pl-6 border-l border-[#FFFFFF]/20">
              <div className="text-right hidden sm:block">
                <div className="text-body-md font-semibold text-[#FFFFFF]">{name}</div>
                <div className="text-label-sm text-[#FFFFFF]">Educator</div>
              </div>
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg">
                <span className="material-symbols-outlined text-secondary text-[22px]">person</span>
              </div>
            </div>
          </div>
        </header>
        <main className="pt-20 p-margin-desktop bg-inverse-surface text-[#FFFFFF]">
          <div className="flex flex-col w-full relative min-h-[800px] font-body-md text-[#FFFFFF] p-6 gap-12">
            {children}
          </div>
        </main>
      </div>
    </>
  );
}
