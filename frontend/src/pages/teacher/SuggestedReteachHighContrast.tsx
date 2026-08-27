/**
 * Converted from stitch_ascent_educator_dashboard/suggested_reteach_high_contrast/suggested_reteach_high_contrast.html
 * Wired live (frontend-003): GET /teacher/reteach (drafts + assigned), POST
 * /teacher/reteach/suggest-top (teacher-008 — drafts the top 3 misconceptions
 * and top 3 gaps in one press; idempotent), POST /teacher/reteach/{id}/approve
 * (an approved unit is what the student's Assignments panel shows).
 *
 * First "draft" press on a cold model cache takes up to a minute of provider
 * calls; every later press is free (disk cache). Do it BEFORE the demo.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  approveReteachUnit,
  cached,
  getReteachUnits,
  invalidateCache,
  suggestTopReteach,
  type ReteachUnitDto,
} from "@/lib/api";

export default function SuggestedReteachHighContrast() {
  const [units, setUnits] = useState<ReteachUnitDto[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drafting, setDrafting] = useState(false);
  const [draftNote, setDraftNote] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = () =>
    cached("reteach", () => getReteachUnits())
      .then((r) => {
        setUnits(r);
        setError(null);
      })
      .catch(() => setError("Could not load reteach units."));

  useEffect(() => {
    load();
  }, []);

  async function draftTop() {
    setDrafting(true);
    setDraftNote("Drafting from the heatmap and gap map — the first press takes up to a minute of model calls…");
    try {
      const r = await suggestTopReteach();
      invalidateCache("reteach");
      await load();
      setDraftNote(
        `Drafted ${r.drafted?.length ?? 0} new unit${(r.drafted?.length ?? 0) === 1 ? "" : "s"}` +
          (r.skipped?.length ? ` · ${r.skipped.length} skipped (already covered or no corpus support)` : ""),
      );
    } catch {
      setDraftNote(null);
      setError("Drafting failed — check the provider and try again.");
    } finally {
      setDrafting(false);
    }
  }

  async function approve(id: number) {
    setBusyId(id);
    try {
      await approveReteachUnit(id);
      invalidateCache("reteach", "assignments");
      await load();
    } catch {
      setError("Could not approve that unit — try again.");
    } finally {
      setBusyId(null);
    }
  }

  const drafts = (units ?? []).filter((u) => u.status === "draft");
  const assigned = (units ?? []).filter((u) => u.status === "assigned");

  const Unit = ({ u }: { u: ReteachUnitDto }) => (
    <article className="bg-surface-container-lowest text-ink p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="font-label-sm text-label-sm uppercase tracking-widest text-ink/60">
            {u.target === "misconception" ? "Misconception reteach" : "Prerequisite reteach"}
          </span>
          <h3 className="font-title-md text-title-md leading-snug mt-1">{u.title || u.label}</h3>
        </div>
        {u.status === "draft" ? (
          <button
            onClick={() => approve(u.id)}
            disabled={busyId === u.id}
            className="shrink-0 bg-primary text-on-primary px-5 py-2.5 rounded-lg font-title-md text-title-md hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">publish</span>
            {busyId === u.id ? "Approving…" : "Approve & assign"}
          </button>
        ) : (
          <span className="shrink-0 bg-secondary-container font-label-sm text-label-sm px-2 py-1 rounded font-semibold">
            ASSIGNED
          </span>
        )}
      </div>
      <p className="font-label-sm text-label-sm text-ink/70">{u.label}</p>
      <p className="font-body-md text-body-md line-clamp-4 text-ink/90 whitespace-pre-line">{u.body}</p>
    </article>
  );

  return (
    <TeacherChrome active="suggested-reteach">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">psychology</span>
            Targeted Intervention
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">
            Suggested Reteach
          </h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            Units drafted from the class's own evidence — the misconception heatmap and the gap map.
            Nothing reaches a student until you approve it.
          </p>
        </div>
        <button
          onClick={draftTop}
          disabled={drafting}
          className="bg-secondary text-ink px-6 py-3 rounded-lg font-title-md text-title-md hover:bg-secondary-fixed transition-colors shadow-sm flex items-center gap-2 disabled:opacity-60"
        >
          <span className="material-symbols-outlined">auto_awesome</span>
          {drafting ? "Drafting…" : "Draft top 3 + top 3"}
        </button>
      </header>

      {error && (
        <p role="alert" className="bg-error/20 text-ink px-6 py-4 rounded-xl">
          {error}
        </p>
      )}
      {draftNote && !error && (
        <p className="border border-secondary/40 bg-secondary/10 text-ink px-6 py-4 rounded-xl">
          {draftNote}
        </p>
      )}

      <section className="relative z-10">
        <h2 className="font-headline-lg text-headline-lg text-ink mb-6">
          Drafts awaiting approval ({drafts.length})
        </h2>
        {drafts.length === 0 ? (
          <p className="font-body-lg text-body-lg text-ink-soft mb-10">
            No drafts. Press "Draft top 3 + top 3" to generate them from the current heatmap and gap
            map.
          </p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
            {drafts.map((u) => (
              <Unit key={u.id} u={u} />
            ))}
          </div>
        )}

        <h2 className="font-headline-lg text-headline-lg text-ink mb-6">
          Assigned to the class ({assigned.length})
        </h2>
        {assigned.length === 0 ? (
          <p className="font-body-lg text-body-lg text-ink-soft">
            Nothing assigned yet. Approved units appear in every affected student's Assignments
            panel.
          </p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {assigned.map((u) => (
              <Unit key={u.id} u={u} />
            ))}
          </div>
        )}
      </section>
    </TeacherChrome>
  );
}
