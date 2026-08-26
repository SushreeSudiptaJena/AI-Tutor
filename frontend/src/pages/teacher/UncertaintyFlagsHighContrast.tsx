/**
 * Converted from stitch_ascent_educator_dashboard/uncertainty_flags_high_contrast/uncertainty_flags_high_contrast.html
 * Wired live (frontend-003): GET /teacher/uncertainty-flags — rows are
 * written automatically by rag-003 whenever the tutor refuses for lack of
 * evidence (and only then). Resolving a flag is the real POST.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import { cached, getUncertaintyFlags, invalidateCache, resolveUncertaintyFlag, type UncertaintyFlagDto } from "@/lib/api";

const REASONS: Record<string, string> = {
  no_matching_material: "No matching material — nothing in the approved books came close",
  material_does_not_answer:
    "Material doesn't answer it — the books touch the topic but never teach this",
};

function since(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  return `${Math.round(mins / 1440)}d ago`;
}

export default function UncertaintyFlagsHighContrast() {
  const [open, setOpen] = useState<UncertaintyFlagDto[] | null>(null);
  const [resolved, setResolved] = useState<UncertaintyFlagDto[] | null>(null);
  const [showResolved, setShowResolved] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () =>
    Promise.all([
      cached("flags-open", () => getUncertaintyFlags("open")),
      cached("flags-resolved", () => getUncertaintyFlags("resolved")),
    ])
      .then(([o, r]) => {
        setOpen(o);
        setResolved(r);
        setError(null);
      })
      .catch(() => setError("Could not load the flags."));

  useEffect(() => {
    load();
  }, []);

  async function resolve(id: number) {
    setBusyId(id);
    try {
      await resolveUncertaintyFlag(id);
      invalidateCache("flags-open", "flags-resolved");
      await load();
    } catch {
      setError("Could not resolve that flag — try again.");
    } finally {
      setBusyId(null);
    }
  }

  const list = showResolved ? resolved ?? [] : open ?? [];

  return (
    <TeacherChrome active="uncertainty-flags">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-[#FFFFFF]/20 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-[#FFFFFF] mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">warning</span>
            Curriculum Coverage
          </span>
          <h1 className="font-display-lg text-display-lg text-[#FFFFFF] m-0 leading-tight">
            Uncertainty Flags
          </h1>
          <p className="font-body-lg text-body-lg text-[#FFFFFF] mt-4 max-w-xl">
            Every question the tutor could not ground in the approved material, and therefore refused
            to answer. Anonymous by design — what the class needs, not who asked.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowResolved(false)}
            className={`px-5 py-3 rounded-lg font-title-md text-title-md transition-colors ${
              !showResolved ? "bg-secondary text-[#1A1A1A]" : "border border-[#FFFFFF]/30 text-[#FFFFFF]"
            }`}
          >
            Open ({open?.length ?? "…"})
          </button>
          <button
            onClick={() => setShowResolved(true)}
            className={`px-5 py-3 rounded-lg font-title-md text-title-md transition-colors ${
              showResolved ? "bg-secondary text-[#1A1A1A]" : "border border-[#FFFFFF]/30 text-[#FFFFFF]"
            }`}
          >
            Resolved ({resolved?.length ?? "…"})
          </button>
        </div>
      </header>

      {error && (
        <p role="alert" className="bg-error/20 text-[#FFFFFF] px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        {list.length === 0 && !error && (
          <p className="font-body-lg text-body-lg text-[#FFFFFF]/70">
            {showResolved
              ? "Nothing resolved yet."
              : "No open flags — everything the class has asked is grounded in the material."}
          </p>
        )}
        {list.map((f) => (
          <article
            key={f.id}
            className="bg-surface-container-lowest text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] flex flex-col gap-4"
          >
            <div className="flex items-start justify-between gap-4">
              <h3 className="font-title-md text-title-md leading-snug">{f.question}</h3>
              <span className="shrink-0 bg-error-container font-label-sm text-label-sm px-2 py-1 rounded font-semibold">
                {f.alignment_percent}% aligned
              </span>
            </div>
            <p className="font-body-md text-body-md text-[#1A1A1A]/80">
              {REASONS[f.reason] ?? f.reason}
            </p>
            <div className="flex items-center justify-between mt-auto pt-4 border-t border-[#1A1A1A]/10">
              <span className="font-label-sm text-label-sm text-[#1A1A1A]/60 uppercase">
                {since(f.occurred_at)} · {f.status}
              </span>
              {f.status === "open" && (
                <button
                  onClick={() => resolve(f.id)}
                  disabled={busyId === f.id}
                  className="bg-primary text-[#FFFFFF] px-5 py-2.5 rounded-lg font-title-md text-title-md hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-[18px]">check_circle</span>
                  {busyId === f.id ? "Resolving…" : "Mark resolved"}
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </TeacherChrome>
  );
}
