/**
 * Converted from stitch_ascent_educator_dashboard/content_verification_high_contrast/content_verification_high_contrast.html
 * Wired live (frontend-004): GET /teacher/verification-queue + approve/reject
 * (teacher-007). Seeded by design — no live web search in this build. A
 * pending item is unreachable from every student endpoint; this queue is the
 * human gate that makes "curriculum-aligned" mean anything.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  approveVerificationItem,
  cached,
  getVerificationQueue,
  invalidateCache,
  rejectVerificationItem,
  type VerificationItem,
} from "@/lib/api";

export default function ContentVerificationHighContrast() {
  const [items, setItems] = useState<VerificationItem[] | null>(null);
  const [showDecided, setShowDecided] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [rejecting, setRejecting] = useState<number | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = () =>
    Promise.all([
      cached("vqueue-pending", () => getVerificationQueue("pending")),
      cached("vqueue-all", () => getVerificationQueue("all")),
    ])
      .then(([pending, all]) => {
        setItems(showDecided ? all : pending);
        setError(null);
      })
      .catch(() => setError("Could not load the verification queue."));

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showDecided]);

  async function approve(id: number) {
    setBusyId(id);
    try {
      await approveVerificationItem(id);
      invalidateCache("vqueue-pending", "vqueue-all");
      await load();
    } catch {
      setError("Could not approve — try again.");
    } finally {
      setBusyId(null);
    }
  }

  async function reject(id: number) {
    setBusyId(id);
    try {
      await rejectVerificationItem(id, reason.trim() || undefined);
      setRejecting(null);
      setReason("");
      invalidateCache("vqueue-pending", "vqueue-all");
      await load();
    } catch {
      setError("Could not reject — try again.");
    } finally {
      setBusyId(null);
    }
  }

  const list = items ?? [];

  return (
    <TeacherChrome active="content-verification">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">verified</span>
            Sourced Content
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">
            Content Verification
          </h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            Material the AI found outside the approved corpus, waiting for a human decision.
            Nothing here reaches a student until you approve it.
          </p>
        </div>
        <button
          onClick={() => setShowDecided((v) => !v)}
          className="border border-ink/25 text-ink px-5 py-3 rounded-lg font-title-md text-title-md hover:border-secondary transition-colors"
        >
          {showDecided ? "Show pending only" : "Show decided too"}
        </button>
      </header>

      {error && (
        <p role="alert" className="bg-error/20 text-ink px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        {list.length === 0 && !error && (
          <p className="font-body-lg text-body-lg text-ink-soft">
            {showDecided ? "Queue is empty." : "Nothing pending — the gate is clear."}
          </p>
        )}
        {list.map((v) => (
          <article
            key={v.id}
            className="bg-surface-container-lowest text-ink p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] flex flex-col gap-4"
          >
            <div className="flex items-start justify-between gap-4">
              <h3 className="font-title-md text-title-md leading-snug">{v.title}</h3>
              <span
                className={`shrink-0 font-label-sm text-label-sm px-2 py-1 rounded font-semibold ${
                  v.status === "pending" ? "bg-error-container" : "bg-secondary-container"
                }`}
              >
                {v.status.toUpperCase()}
              </span>
            </div>
            <p className="font-body-md text-body-md text-ink/85 line-clamp-4">{v.excerpt}</p>
            <p className="font-label-sm text-label-sm text-ink/60 flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">travel_explore</span>
              Found for: <strong>{v.found_for_gap}</strong>
            </p>
            <a
              href={v.source_url}
              target="_blank"
              rel="noreferrer"
              className="font-label-sm text-label-sm underline flex items-center gap-1 w-fit"
            >
              <span className="material-symbols-outlined text-[16px]">open_in_new</span>
              {v.source_url.replace(/^https?:\/\//, "").slice(0, 60)}
            </a>

            {v.status === "pending" ? (
              rejecting === v.id ? (
                <div className="flex flex-col gap-2 mt-2">
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Why is this being rejected? (kept on the row)"
                    className="w-full px-4 py-2.5 rounded-lg border border-ink/20 bg-card text-ink outline-none focus:border-primary"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => reject(v.id)}
                      disabled={busyId === v.id}
                      className="bg-error text-on-primary px-5 py-2.5 rounded-lg font-title-md text-title-md disabled:opacity-50"
                    >
                      {busyId === v.id ? "Rejecting…" : "Confirm reject"}
                    </button>
                    <button
                      onClick={() => {
                        setRejecting(null);
                        setReason("");
                      }}
                      className="border border-ink/20 px-5 py-2.5 rounded-lg font-title-md text-title-md"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => approve(v.id)}
                    disabled={busyId === v.id}
                    className="bg-primary text-on-primary px-5 py-2.5 rounded-lg font-title-md text-title-md hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined text-[18px]">check_circle</span>
                    {busyId === v.id ? "Approving…" : "Approve"}
                  </button>
                  <button
                    onClick={() => setRejecting(v.id)}
                    className="border border-error/50 text-error px-5 py-2.5 rounded-lg font-title-md text-title-md hover:bg-error/5 transition-colors"
                  >
                    Reject…
                  </button>
                </div>
              )
            ) : (
              v.reject_reason && (
                <p className="font-label-sm text-label-sm text-ink/60 mt-2">
                  Rejected: {v.reject_reason}
                </p>
              )
            )}
          </article>
        ))}
      </div>
    </TeacherChrome>
  );
}
