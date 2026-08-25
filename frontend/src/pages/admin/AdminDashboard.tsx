import React, { useEffect, useState } from "react";

/**
 * AdminDashboard.tsx
 * ---------------------------------------------------------------------------
 * Merges the three standalone admin screens (Curriculum Upload, Course
 * Structure, Audit Log) into ONE component with client-side tab navigation,
 * so the sidebar links flow "next to next to next" instead of loading
 * separate pages.
 *
 * NOTE ON STYLING:
 * The original HTML files used the Tailwind CDN script with a custom inline
 * theme (colors like `bg-surface`, `text-tertiary`, etc.). Your Vite project
 * almost certainly has its own Tailwind build, so those custom class names
 * won't resolve unless you either:
 *   (a) merge the `THEME_CONFIG` below into your real tailwind.config.js, or
 *   (b) keep the <script> injection below (quick way to get it working today).
 * This file does (b) by default so you can drop it in and see it work, then
 * migrate to (a) whenever you wire up your real Tailwind config.
 * ---------------------------------------------------------------------------
 */

type TabKey = "upload" | "structure" | "audit";

const NAV_ITEMS: { key: TabKey; label: string; icon: string }[] = [
  { key: "upload", label: "Curriculum Upload", icon: "cloud_upload" },
  { key: "structure", label: "Course Structure", icon: "account_tree" },
  { key: "audit", label: "Audit Log", icon: "receipt_long" },
];

const THEME_CONFIG = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "outline-variant": "#43474a",
        "surface-container-high": "#282a2b",
        "secondary-fixed-dim": "#b0c9e9",
        "surface-dim": "#121414",
        "surface-container-low": "#1a1c1c",
        "surface-bright": "#38393a",
        "primary-container": "#243138",
        "on-tertiary": "#1e3700",
        "on-error": "#690005",
        secondary: "#b0c9e9",
        "on-secondary-fixed": "#001d35",
        "surface-tint": "#bbc9d1",
        "on-primary-container": "#8b99a1",
        "on-background": "#e2e2e2",
        surface: "#121414",
        "on-secondary-fixed-variant": "#304863",
        "on-tertiary-container": "#70a62f",
        "secondary-container": "#304863",
        "on-tertiary-fixed-variant": "#2e4f00",
        "on-primary-fixed-variant": "#3b4950",
        "on-tertiary-fixed": "#0f2000",
        "surface-container-highest": "#333535",
        "on-error-container": "#ffdad6",
        "on-secondary-container": "#9fb7d7",
        primary: "#bbc9d1",
        "on-secondary": "#18324c",
        "error-container": "#93000a",
        "on-primary": "#253239",
        "surface-variant": "#333535",
        error: "#ffb4ab",
        background: "#121414",
        "primary-fixed": "#d6e5ee",
        outline: "#8d9194",
        "secondary-fixed": "#d1e4ff",
        "on-surface-variant": "#c3c7ca",
        tertiary: "#9dd75b",
        "inverse-primary": "#536068",
        "inverse-on-surface": "#2f3131",
        "on-primary-fixed": "#101d24",
        "tertiary-fixed-dim": "#9dd75b",
        "surface-container": "#1e2020",
        "on-surface": "#e2e2e2",
        "tertiary-container": "#1e3600",
        "surface-container-lowest": "#0c0f0f",
        "primary-fixed-dim": "#bbc9d1",
        "inverse-surface": "#e2e2e2",
        "tertiary-fixed": "#b8f473",
      },
      borderRadius: { DEFAULT: "0.25rem", lg: "0.5rem", xl: "0.75rem", full: "9999px" },
      spacing: {
        "section-gap": "48px",
        gutter: "24px",
        unit: "8px",
        "card-inner-padding": "24px",
        "container-padding": "32px",
      },
      fontFamily: {
        "headline-md": ["Hanken Grotesk"],
        "headline-sm": ["Hanken Grotesk"],
        "display-lg": ["Hanken Grotesk"],
        "label-sm": ["Hanken Grotesk"],
        "headline-lg-mobile": ["Hanken Grotesk"],
        "body-lg": ["Hanken Grotesk"],
        "label-md": ["Hanken Grotesk"],
        "body-md": ["Hanken Grotesk"],
        "headline-lg": ["Hanken Grotesk"],
      },
      fontSize: {
        "headline-md": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "headline-sm": ["20px", { lineHeight: "28px", fontWeight: "500" }],
        "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "label-sm": ["12px", { lineHeight: "16px", letterSpacing: "0.04em", fontWeight: "500" }],
        "headline-lg-mobile": ["28px", { lineHeight: "36px", fontWeight: "600" }],
        "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "label-md": ["14px", { lineHeight: "20px", letterSpacing: "0.01em", fontWeight: "600" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "headline-lg": ["32px", { lineHeight: "40px", fontWeight: "600" }],
      },
    },
  },
};

/** Injects the Tailwind CDN + custom theme + Material Symbols + font once. */
function useDesignSystemBootstrap() {
  useEffect(() => {
    if (document.getElementById("ns-tailwind-cdn")) return;

    const fonts = document.createElement("link");
    fonts.rel = "stylesheet";
    fonts.href =
      "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap";
    document.head.appendChild(fonts);

    const cdn = document.createElement("script");
    cdn.id = "ns-tailwind-cdn";
    cdn.src = "https://cdn.tailwindcss.com?plugins=forms,container-queries";
    cdn.onload = () => {
      // @ts-ignore - injected globally by the CDN script
      window.tailwind.config = THEME_CONFIG;
    };
    document.head.appendChild(cdn);

    const style = document.createElement("style");
    style.id = "ns-custom-style";
    style.innerHTML = `
      .ns-glass-card {
        background: rgba(18, 20, 20, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
      }
      .ns-glass-panel {
        background: rgba(36, 49, 56, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05);
      }
      .ns-ai-accent-glow { box-shadow: 0 0 20px rgba(122, 177, 57, 0.3); }
      .ns-btn-primary {
        background: linear-gradient(135deg, #1e3600, #2e4f00);
        border: 1px solid rgba(157, 215, 91, 0.2);
        color: #b8f473;
      }
      .ns-btn-primary:hover {
        background: linear-gradient(135deg, #2e4f00, #1e3600);
        box-shadow: 0 0 15px rgba(157, 215, 91, 0.2);
      }
      .ns-custom-scrollbar::-webkit-scrollbar { width: 8px; height: 8px; }
      .ns-custom-scrollbar::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 4px; }
      .ns-custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
      .ns-custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
    `;
    document.head.appendChild(style);
  }, []);
}

function useLiveClock() {
  const [clock, setClock] = useState(() => formatClock());
  useEffect(() => {
    const id = setInterval(() => setClock(formatClock()), 60000);
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

function TopBar({ title }: { title: string }) {
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
            <span className="font-label-md text-label-md text-tertiary">Julian Admin</span>
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
function CurriculumUploadView() {
  return (
    <div className="flex-1 overflow-y-auto p-gutter md:p-section-gap ns-custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-section-gap pb-32">
        <div>
          <h1 className="font-display-lg text-display-lg text-on-surface mb-2">Curriculum Upload</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Ingest, version, and map scholarly texts to course structures.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
          <div className="lg:col-span-7 flex flex-col gap-gutter">
            <section className="ns-glass-panel rounded-xl p-card-inner-padding">
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4 flex items-center gap-2">
                <Icon name="upload_file" className="text-tertiary" />
                Source Material Ingestion
              </h2>
              <div className="border-2 border-dashed border-outline-variant/50 rounded-lg p-8 flex flex-col items-center justify-center text-center bg-surface-container-low/30 hover:bg-surface-container-low/60 hover:border-tertiary/50 transition-all cursor-pointer group">
                <div className="bg-surface-container-high p-4 rounded-full mb-4 group-hover:scale-110 transition-transform shadow-lg shadow-black/20">
                  <Icon name="note_add" className="text-3xl text-on-surface-variant group-hover:text-tertiary transition-colors" />
                </div>
                <h3 className="font-headline-md text-headline-md text-on-surface mb-2">Drag &amp; Drop Documents</h3>
                <p className="font-body-md text-body-md text-on-surface-variant mb-6 max-w-sm">
                  Support for PDF, DOCX, and TXT files. Max file size: 50MB per document.
                </p>
                <button className="px-6 py-2.5 bg-surface-container-high text-on-surface font-label-md text-label-md rounded-full border border-outline-variant/30 hover:bg-surface-bright transition-colors flex items-center gap-2 shadow-sm">
                  Browse Files
                </button>
              </div>
            </section>

            <section className="ns-glass-panel rounded-xl p-card-inner-padding">
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-6 flex items-center gap-2">
                <Icon name="account_tree" className="text-tertiary" />
                Content Mapping Strategy
              </h2>
              <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
                <div>
                  <label className="block font-label-md text-label-md text-on-surface-variant mb-2">Target Course</label>
                  <select className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-4 py-2.5 font-body-md text-body-md text-on-surface focus:border-tertiary focus:ring-1 focus:ring-tertiary outline-none">
                    <option>Advanced Quantum Mechanics (PHY-401)</option>
                    <option>Computational Linguistics (CS-302)</option>
                    <option>Synthetic Biology Foundations (BIO-510)</option>
                  </select>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block font-label-md text-label-md text-on-surface-variant mb-2">Module / Chapter</label>
                    <select className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-4 py-2.5 font-body-md text-body-md text-on-surface focus:border-tertiary focus:ring-1 focus:ring-tertiary outline-none">
                      <option>Module 4: Entanglement Dynamics</option>
                      <option>Module 5: Decoherence</option>
                      <option>New Module...</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-label-md text-label-md text-on-surface-variant mb-2">Content Type</label>
                    <select className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg px-4 py-2.5 font-body-md text-body-md text-on-surface focus:border-tertiary focus:ring-1 focus:ring-tertiary outline-none">
                      <option>Core Syllabus</option>
                      <option>Required Reading</option>
                      <option>Supplementary Notes</option>
                    </select>
                  </div>
                </div>
                <div className="pt-4 flex justify-end">
                  <button
                    type="submit"
                    className="px-6 py-2.5 bg-gradient-to-r from-tertiary-container to-[#4a6b20] text-tertiary font-label-md text-label-md rounded-full hover:shadow-[0_0_15px_rgba(112,166,47,0.3)] transition-all flex items-center gap-2"
                  >
                    <Icon name="add_link" className="text-sm" />
                    Map to Syllabus
                  </button>
                </div>
              </form>
            </section>
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
                    <p className="font-label-md text-label-md text-on-surface-variant">Storage Utilization</p>
                    <p className="font-headline-md text-headline-md text-on-surface">
                      42.5 GB <span className="font-body-md text-body-md text-on-surface-variant">/ 100 GB</span>
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-outline-variant/10">
                  <h3 className="font-label-md text-label-md text-on-surface-variant mb-4 uppercase tracking-wider">
                    Recent Ingestions
                  </h3>
                  <ul className="space-y-3">
                    <li className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-tertiary mt-2" />
                      <div>
                        <p className="font-body-md text-body-md text-on-surface text-sm">Quantum_Mechanics_v3.pdf</p>
                        <p className="font-label-sm text-label-sm text-on-surface-variant">
                          Mapped to PHY-401 by Julian Admin • 2h ago
                        </p>
                      </div>
                    </li>
                    <li className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-tertiary mt-2" />
                      <div>
                        <p className="font-body-md text-body-md text-on-surface text-sm">Bio_Ethics_Syllabus_2024.docx</p>
                        <p className="font-label-sm text-label-sm text-on-surface-variant">
                          Mapped to BIO-510 by Sarah Chen • 5h ago
                        </p>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </section>
          </div>
        </div>

        <section className="ns-glass-panel rounded-xl p-card-inner-padding mt-section-gap overflow-hidden">
          <div className="flex justify-between items-end mb-6">
            <div>
              <h2 className="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
                <Icon name="commit" className="text-tertiary" />
                Document Version Control
              </h2>
              <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                Audit log of all curriculum uploads and iterative revisions.
              </p>
            </div>
            <button className="hidden sm:flex px-4 py-2 bg-surface-container-high text-on-surface font-label-md text-label-md rounded-full border border-outline-variant/30 hover:bg-surface-bright transition-colors items-center gap-2">
              <Icon name="filter_list" className="text-sm" />
              Filter Log
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="border-b border-outline-variant/20">
                  <th className="py-3 px-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Document Name</th>
                  <th className="py-3 px-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Course Target</th>
                  <th className="py-3 px-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Version</th>
                  <th className="py-3 px-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Date &amp; Time</th>
                  <th className="py-3 px-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Uploader</th>
                  <th className="py-3 px-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                {[
                  { icon: "picture_as_pdf", iconColor: "text-error", name: "Advanced_QM_Notes.pdf", course: "PHY-401", version: "v2.1", versionActive: true, date: "Oct 24, 2023 14:30", uploader: "Julian Admin", faded: false },
                  { icon: "description", iconColor: "text-secondary", name: "CS302_Syllabus_Final.docx", course: "CS-302", version: "v1.0", versionActive: false, date: "Oct 22, 2023 09:15", uploader: "Elena Rostova", faded: false },
                  { icon: "picture_as_pdf", iconColor: "text-error", name: "Advanced_QM_Notes_Draft.pdf", course: "PHY-401", version: "v1.0", versionActive: false, date: "Oct 20, 2023 16:45", uploader: "Julian Admin", faded: true },
                ].map((row) => (
                  <tr key={row.name} className={"hover:bg-surface-container-high/30 transition-colors " + (row.faded ? "opacity-60" : "")}>
                    <td className="py-4 px-4 font-body-md text-body-md text-on-surface flex items-center gap-3">
                      <Icon name={row.icon} className={row.iconColor} />
                      {row.name}
                    </td>
                    <td className="py-4 px-4 font-body-md text-body-md text-on-surface-variant">{row.course}</td>
                    <td className="py-4 px-4">
                      <span
                        className={
                          "inline-block px-2 py-1 rounded font-label-sm text-label-sm border " +
                          (row.versionActive
                            ? "bg-tertiary-container/30 text-tertiary border-tertiary/20"
                            : "bg-surface-container-highest text-on-surface-variant border-outline-variant/30")
                        }
                      >
                        {row.version}
                      </span>
                    </td>
                    <td className="py-4 px-4 font-body-md text-body-md text-on-surface-variant text-sm">{row.date}</td>
                    <td className="py-4 px-4 font-body-md text-body-md text-on-surface">{row.uploader}</td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="p-1.5 text-on-surface-variant hover:text-tertiary transition-colors rounded hover:bg-surface-container-high" title="View Document">
                          <Icon name="visibility" className="text-[20px]" />
                        </button>
                        <button className="p-1.5 text-on-surface-variant hover:text-tertiary transition-colors rounded hover:bg-surface-container-high" title="Download">
                          <Icon name="download" className="text-[20px]" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Tab 2: Course & Institution Structure                                     */
/* ------------------------------------------------------------------------ */
function CourseStructureView() {
  return (
    <main className="flex-1 p-gutter md:p-container-padding overflow-y-auto w-full max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-section-gap gap-6">
        <div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface mb-2">Course &amp; Institution Structure</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Manage departments, academic programs, and prerequisites.
          </p>
        </div>
        <div className="flex gap-4 w-full md:w-auto">
          <button className="ns-btn-primary flex-1 md:flex-none px-6 py-3 rounded-full font-label-md text-label-md flex items-center justify-center gap-2 transition-all">
            <Icon name="add" className="text-sm" />
            Add Department
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        <div className="xl:col-span-8 space-y-6">
          {/* Department: Computer Science */}
          <div className="ns-glass-card rounded-[24px] p-card-inner-padding relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-secondary/5 rounded-full blur-3xl -mt-32 -mr-32 pointer-events-none" />
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center justify-center border border-outline-variant/20">
                  <Icon name="terminal" className="text-secondary" />
                </div>
                <div>
                  <h3 className="font-headline-md text-headline-md text-on-surface">Computer Science</h3>
                  <p className="font-label-sm text-label-sm text-on-surface-variant mt-1">School of Engineering</p>
                </div>
              </div>
              <button className="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-bright flex items-center justify-center transition-colors text-on-surface-variant">
                <Icon name="more_vert" className="text-[20px]" />
              </button>
            </div>

            <div className="space-y-3 relative pl-6 before:absolute before:left-[23px] before:top-2 before:bottom-2 before:w-px before:bg-outline-variant/20">
              <div className="bg-surface/50 border border-outline-variant/10 rounded-xl p-4 flex items-center justify-between hover:border-outline-variant/30 transition-colors relative">
                <div className="absolute left-[-24px] top-1/2 w-6 h-px bg-outline-variant/20" />
                <div>
                  <h4 className="font-headline-sm text-headline-sm text-on-surface">CS101: Introduction to AI</h4>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-secondary-container/30 border border-secondary/20 font-label-sm text-label-sm text-secondary-fixed">
                      <Icon name="link" className="text-[14px]" />
                      Requires: CS100 Intro to Programming
                    </span>
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container-high border border-outline-variant/20 font-label-sm text-label-sm text-on-surface-variant">
                      4 Credits
                    </span>
                  </div>
                </div>
                <button className="text-on-surface-variant hover:text-tertiary transition-colors">
                  <Icon name="edit" />
                </button>
              </div>

              <div className="bg-surface/50 border border-outline-variant/10 rounded-xl p-4 flex items-center justify-between hover:border-outline-variant/30 transition-colors relative">
                <div className="absolute left-[-24px] top-1/2 w-6 h-px bg-outline-variant/20" />
                <div>
                  <h4 className="font-headline-sm text-headline-sm text-on-surface">CS205: Advanced Neural Networks</h4>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-error-container/20 border border-error/20 font-label-sm text-label-sm text-error">
                      <Icon name="lock" className="text-[14px]" />
                      Requires: CS101, MTH201
                    </span>
                  </div>
                </div>
                <button className="text-on-surface-variant hover:text-tertiary transition-colors">
                  <Icon name="edit" />
                </button>
              </div>
            </div>

            <button className="mt-4 ml-6 flex items-center gap-2 font-label-md text-label-md text-tertiary hover:text-tertiary-fixed transition-colors">
              <Icon name="add_circle" className="text-[18px]" />
              Add Course to CS
            </button>
          </div>

          {/* Department: Literature */}
          <div className="ns-glass-card rounded-[24px] p-card-inner-padding relative overflow-hidden">
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center justify-center border border-outline-variant/20">
                  <Icon name="menu_book" className="text-tertiary" />
                </div>
                <div>
                  <h3 className="font-headline-md text-headline-md text-on-surface">Literature</h3>
                  <p className="font-label-sm text-label-sm text-on-surface-variant mt-1">School of Humanities</p>
                </div>
              </div>
              <button className="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-bright flex items-center justify-center transition-colors text-on-surface-variant">
                <Icon name="more_vert" className="text-[20px]" />
              </button>
            </div>

            <div className="space-y-3 relative pl-6 before:absolute before:left-[23px] before:top-2 before:bottom-2 before:w-px before:bg-outline-variant/20">
              <div className="bg-surface/50 border border-outline-variant/10 rounded-xl p-4 flex items-center justify-between hover:border-outline-variant/30 transition-colors relative">
                <div className="absolute left-[-24px] top-1/2 w-6 h-px bg-outline-variant/20" />
                <div>
                  <h4 className="font-headline-sm text-headline-sm text-on-surface">LIT210: Romantic Poetry</h4>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container-high border border-outline-variant/20 font-label-sm text-label-sm text-on-surface-variant">
                      No prerequisites
                    </span>
                  </div>
                </div>
                <button className="text-on-surface-variant hover:text-tertiary transition-colors">
                  <Icon name="edit" />
                </button>
              </div>
            </div>

            <button className="mt-4 ml-6 flex items-center gap-2 font-label-md text-label-md text-tertiary hover:text-tertiary-fixed transition-colors">
              <Icon name="add_circle" className="text-[18px]" />
              Add Course to Literature
            </button>
          </div>
        </div>

        <div className="xl:col-span-4 space-y-6">
          <div className="ns-glass-card rounded-[24px] p-card-inner-padding">
            <h3 className="font-headline-sm text-headline-sm text-on-surface mb-6 border-b border-outline-variant/20 pb-4">Overview</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface-container rounded-xl p-4 border border-outline-variant/10">
                <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Total Depts</p>
                <p className="font-display-lg text-display-lg text-on-surface">12</p>
              </div>
              <div className="bg-surface-container rounded-xl p-4 border border-outline-variant/10">
                <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Total Courses</p>
                <p className="font-display-lg text-display-lg text-secondary">148</p>
              </div>
            </div>
          </div>

          <div className="ns-glass-card rounded-[24px] p-card-inner-padding border-tertiary/20 ns-ai-accent-glow">
            <div className="flex items-center gap-3 mb-4">
              <Icon name="psychology" className="text-tertiary" />
              <h3 className="font-headline-sm text-headline-sm text-on-surface">AI Structural Insights</h3>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant mb-4">
              Dependency analysis indicates a potential bottleneck in{" "}
              <span className="text-on-surface font-semibold">CS100 Intro to Programming</span>, required by 85% of
              advanced STEM courses. Consider adding parallel introductory tracks.
            </p>
            <button className="text-tertiary font-label-md text-label-md flex items-center gap-1 hover:text-tertiary-fixed transition-colors">
              View Dependency Graph <Icon name="arrow_forward" className="text-[16px]" />
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

/* ------------------------------------------------------------------------ */
/* Tab 3: Audit Log                                                          */
/* ------------------------------------------------------------------------ */
function AuditLogView() {
  const rows = [
    { date: "Oct 24, 2023", time: "22:45:12", admin: "Julian Admin", isSystem: false, action: <>Uploaded new version of <span className="text-tertiary">Ch 3 notes</span></>, targetIcon: "folder", target: "CS101", status: "Success" as const },
    { date: "Oct 24, 2023", time: "19:30:05", admin: "System", isSystem: true, action: "Automated nightly backup completed", targetIcon: "database", target: "Global", status: "Success" as const },
    { date: "Oct 24, 2023", time: "14:15:22", admin: "Julian Admin", isSystem: false, action: "Modified permission settings for guest cohort", targetIcon: "group", target: "Access Ctrl", status: "Override" as const },
    { date: "Oct 23, 2023", time: "09:05:11", admin: "Julian Admin", isSystem: false, action: "Deleted obsolete syllabus artifact", targetIcon: "folder", target: "PHY202", status: "Success" as const },
  ];

  return (
    <div className="flex-1 overflow-y-auto ns-custom-scrollbar p-section-gap">
      <div className="ns-glass-card rounded-xl p-4 mb-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4 flex-1">
          <div className="relative w-full max-w-sm">
            <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]" />
            <input
              className="w-full bg-surface-container-low border border-outline-variant/30 rounded-full py-2 pl-10 pr-4 text-on-surface placeholder-on-surface-variant focus:outline-none focus:border-tertiary focus:ring-1 focus:ring-tertiary font-body-md text-body-md transition-all"
              placeholder="Search logs..."
              type="text"
            />
          </div>
          <div className="w-px h-6 bg-outline-variant/30 hidden md:block" />
          <div className="flex items-center gap-2">
            <select className="bg-transparent border border-outline-variant/30 rounded-full py-1.5 pl-4 pr-8 text-on-surface-variant focus:outline-none focus:border-tertiary font-label-md text-label-md appearance-none">
              <option>All Admins</option>
              <option>Julian Admin</option>
              <option>System</option>
            </select>
            <select className="bg-transparent border border-outline-variant/30 rounded-full py-1.5 pl-4 pr-8 text-on-surface-variant focus:outline-none focus:border-tertiary font-label-md text-label-md appearance-none">
              <option>All Courses</option>
              <option>CS101</option>
              <option>PHY202</option>
            </select>
            <button className="flex items-center gap-2 border border-outline-variant/30 rounded-full py-1.5 px-4 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 transition-colors font-label-md text-label-md">
              <Icon name="calendar_month" className="text-[18px]" />
              Date Range
            </button>
          </div>
        </div>
        <button className="flex items-center gap-2 text-tertiary font-label-md text-label-md hover:opacity-80 transition-opacity">
          <Icon name="download" className="text-[20px]" />
          Export CSV
        </button>
      </div>

      <div className="ns-glass-card rounded-2xl overflow-hidden shadow-lg border border-outline-variant/20">
        <div className="p-6 border-b border-outline-variant/10 flex justify-between items-center bg-surface-container-low/50">
          <h3 className="font-headline-sm text-headline-sm font-semibold text-on-surface">System Action Trail</h3>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
            <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Live Monitoring</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant/20 bg-surface-container-high/30">
                <th className="py-4 px-6 font-label-md text-label-md text-on-surface-variant font-semibold">Timestamp</th>
                <th className="py-4 px-6 font-label-md text-label-md text-on-surface-variant font-semibold">Admin</th>
                <th className="py-4 px-6 font-label-md text-label-md text-on-surface-variant font-semibold">Action</th>
                <th className="py-4 px-6 font-label-md text-label-md text-on-surface-variant font-semibold">Target Object</th>
                <th className="py-4 px-6 font-label-md text-label-md text-on-surface-variant font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody className="font-body-md text-body-md divide-y divide-outline-variant/10">
              {rows.map((row, i) => (
                <tr key={i} className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="py-4 px-6 text-on-surface-variant whitespace-nowrap">
                    <div className="flex flex-col">
                      <span>{row.date}</span>
                      <span className="text-sm opacity-70">{row.time}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-surface-container-highest border border-outline-variant/30 overflow-hidden flex-shrink-0 flex items-center justify-center">
                        {row.isSystem ? (
                          <Icon name="settings" className="text-[16px] text-on-surface-variant" />
                        ) : (
                          <span className="text-[10px] text-on-surface-variant">JA</span>
                        )}
                      </div>
                      <span className="text-on-surface">{row.admin}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-on-surface">{row.action}</td>
                  <td className="py-4 px-6">
                    <span
                      className={
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-sm text-label-sm border " +
                        (row.isSystem
                          ? "bg-surface-variant/50 text-on-surface-variant border-outline-variant/30"
                          : "bg-secondary-container/30 text-on-secondary-container border-secondary-container/50")
                      }
                    >
                      <Icon name={row.targetIcon} className="text-[14px]" />
                      {row.target}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <span className={"inline-flex items-center gap-1 " + (row.status === "Success" ? "text-tertiary" : "text-error")}>
                      <Icon name={row.status === "Success" ? "check_circle" : "warning"} className="text-[16px]" />
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t border-outline-variant/10 flex items-center justify-between bg-surface-container-low/30">
          <span className="font-label-sm text-label-sm text-on-surface-variant">Showing 1-4 of 1,284 entries</span>
          <div className="flex items-center gap-2">
            <button className="w-8 h-8 flex items-center justify-center rounded-full border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container-high transition-colors disabled:opacity-50">
              <Icon name="chevron_left" className="text-[18px]" />
            </button>
            <button className="w-8 h-8 flex items-center justify-center rounded-full bg-tertiary-container/20 text-tertiary border border-tertiary/30 font-label-md text-label-md">1</button>
            <button className="w-8 h-8 flex items-center justify-center rounded-full border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container-high transition-colors font-label-md text-label-md">2</button>
            <button className="w-8 h-8 flex items-center justify-center rounded-full border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container-high transition-colors font-label-md text-label-md">3</button>
            <span className="text-on-surface-variant px-1">...</span>
            <button className="w-8 h-8 flex items-center justify-center rounded-full border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container-high transition-colors disabled:opacity-50">
              <Icon name="chevron_right" className="text-[18px]" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------------ */
/* Root component                                                            */
/* ------------------------------------------------------------------------ */
const TITLES: Record<TabKey, string> = {
  upload: "Curriculum Upload",
  structure: "Course & Institution Structure",
  audit: "Audit Log & Version History",
};

export default function AdminDashboard() {
  useDesignSystemBootstrap();
  const [activeTab, setActiveTab] = useState<TabKey>("upload");

  return (
    <div className="dark font-body-md text-body-md bg-background text-on-background min-h-screen flex">
      <Sidebar active={activeTab} onSelect={setActiveTab} />
      <div className="flex-1 flex flex-col ml-64 h-screen overflow-hidden">
        <TopBar title={TITLES[activeTab]} />
        {activeTab === "upload" && <CurriculumUploadView />}
        {activeTab === "structure" && <CourseStructureView />}
        {activeTab === "audit" && <AuditLogView />}
      </div>
    </div>
  );
}
