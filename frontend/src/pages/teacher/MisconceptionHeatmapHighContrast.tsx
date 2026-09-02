/**
 * Converted from stitch_ascent_educator_dashboard/misconception_heatmap_high_contrast/misconception_heatmap_high_contrast.html
 * Wired live (frontend-003): GET /teacher/misconceptions/heatmap, polled
 * every 5s per the contract -- the number moves when a student confirms a
 * diagnosis on another laptop. Share bands drive the impact colouring.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import { cached, getHeatmap, invalidateCache, type Heatmap } from "@/lib/api";

// Slower than the original 5s. The first paint comes from the session cache,
// so the poll only has to catch a change -- it is not what fills the screen.
const POLL_MS = 20000;

// Four bands, four colours. MODERATE and LOW used to share bg-surface-variant
// and bg-outline-variant exactly, so half the scale rendered identically and
// the chip was the only thing telling them apart -- which defeats the point of
// a heat map. Red / orange / green / grey reads as a severity ramp without
// having to consult a legend.
function band(share: number): {
  label: string;
  chip: string;
  text: string;
  bar: string;
} {
  if (share >= 0.3)
    return { label: "CRITICAL", chip: "bg-error-container", text: "text-error", bar: "bg-error" };
  if (share >= 0.15)
    return { label: "HIGH", chip: "bg-peach", text: "text-orange", bar: "bg-orange" };
  if (share >= 0.05)
    return {
      label: "MODERATE",
      chip: "bg-secondary-container",
      text: "text-secondary",
      bar: "bg-secondary",
    };
  return {
    label: "LOW",
    chip: "bg-surface-variant",
    text: "text-ink-faint",
    bar: "bg-outline-variant",
  };
}

function since(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  return `${hrs}h ago`;
}

export default function MisconceptionHeatmapHighContrast() {
  const [data, setData] = useState<Heatmap | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    // Instant: whatever this session already fetched. The panel is on screen
    // before the network answers -- that is the point of the cache.
    cached("heatmap-teacher", getHeatmap)
      .then((d) => alive && (setData(d), setError(null)))
      .catch(() => alive && setError("Could not load the heatmap."));

    // Then poll, but only re-render when something actually MOVED. Setting
    // state every tick re-rendered the whole table three times a minute for
    // nothing, and made "last updated" jump while the class sat still.
    const tick = () =>
      getHeatmap()
        .then((fresh) => {
          if (!alive) return;
          setError(null);
          setData((prev) => {
            const unchanged =
              prev !== null &&
              prev.class_size === fresh.class_size &&
              prev.items.length === fresh.items.length &&
              prev.items.every(
                (it, i) =>
                  it.misconception_id === fresh.items[i].misconception_id &&
                  it.confirmed_count === fresh.items[i].confirmed_count,
              );
            if (unchanged) return prev;
            // the cache feeds the next mount, so it must not go stale
            invalidateCache("heatmap-teacher");
            return fresh;
          });
        })
        .catch(() => {
          /* a failed poll must never blank a panel that is already correct */
        });

    const timer = setInterval(tick, POLL_MS);
    // Returning to the tab is the cheapest signal that time has passed and
    // the class may have practised since.
    const onFocus = () => tick();
    window.addEventListener("focus", onFocus);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener("focus", onFocus);
    };
  }, []);

  const items = data?.items ?? [];
  const top = items[0];
  const max = Math.max(...items.map((i) => i.share), 0.01);

  return (
    <TeacherChrome active="misconception-heatmap">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-secondary">thermostat</span>
            Cognitive Analytics
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">
            Misconception Heatmap
          </h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            Only diagnoses a student CONFIRMED as their own reasoning are counted. Updates live as the class practises.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex flex-col text-right">
            <span className="font-title-md text-title-md text-ink">
              Class size: {data?.class_size ?? "…"}
            </span>
            <span className="font-label-sm text-label-sm text-ink">
              Last updated: {data ? since(data.updated_at) : "…"}
            </span>
          </div>
        </div>
      </header>

      {error && (
        <p role="alert" className="bg-error/20 text-ink px-6 py-4 rounded-xl">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10">
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-tertiary-fixed text-ink p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
            <div className="absolute -right-12 -top-12 w-40 h-40 bg-secondary/10 rounded-full blur-2xl group-hover:bg-secondary/20 transition-colors"></div>
            <h3 className="font-title-md text-title-md mb-6 pb-4 border-b border-tertiary-fixed-dim/50 flex justify-between items-center text-ink">
              Primary Intervention Target
              <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
                warning
              </span>
            </h3>
            {top ? (
              <div className="flex flex-col gap-2">
                <span className="font-display-lg text-display-lg text-ink">
                  {Math.round(top.share * 100)}%
                </span>
                <span className="font-body-md text-body-md text-ink">
                  of the class consistently demonstrated flawed reasoning in:
                </span>
                <strong className="font-title-md text-title-md mt-2 text-ink">{top.label}</strong>
              </div>
            ) : (
              <p className="font-body-md text-body-md text-ink">
                No confirmed misconceptions yet — the map fills as students practise and confirm what
                the diagnostic surfaced.
              </p>
            )}
          </div>

          {/* The "Overall Impact Distribution" bar chart lived here and is
              gone at the owner's request. It plotted three counts as three
              bars whose widths were each count over the SAME total, so the
              bars did not sum to anything and the chart said nothing the
              coloured band chips on the list do not already say. */}
          {/* What replaced it: the key to the colours, which is the one thing
              the chart was standing in for. */}
          <div className="bg-surface-container-lowest text-ink p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)]">
            <h3 className="font-title-md text-title-md mb-1">Reading the colours</h3>
            <p className="font-body-md text-body-md text-ink/70 mb-6 pb-4 border-b border-ink/10">
              The band is the share of the class who confirmed that misconception — not a guess,
              their own answer to “is this what you were thinking?”.
            </p>
            <ul className="flex flex-col gap-3">
              {[
                { share: 0.35, when: "30% or more of the class", do: "reteach before moving on" },
                { share: 0.2, when: "15–29%", do: "worth a worked example in class" },
                { share: 0.08, when: "5–14%", do: "address in review" },
                { share: 0.01, when: "under 5%", do: "monitor" },
              ].map((row) => {
                const b = band(row.share);
                return (
                  <li key={b.label} className="flex items-start gap-3">
                    <span
                      className={`${b.chip} ${b.text} font-label-sm text-label-sm px-2 py-1 rounded font-semibold shrink-0 w-24 text-center`}
                    >
                      {b.label}
                    </span>
                    <span className="font-body-md text-body-md text-ink/80 leading-snug">
                      {row.when} — {row.do}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
          {/* Was a decorative stock image on a googleusercontent URL that has
              since expired -- a gradient keeps the tile with zero network. */}
          <div className="rounded-2xl overflow-hidden h-48 relative shadow-md">
            <div className="absolute inset-0 bg-gradient-to-br from-tertiary-fixed via-surface-tint/40 to-inverse-surface"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="material-symbols-outlined text-ink/40 text-[64px]">insights</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-8 flex flex-col">
          <div className="bg-tertiary-fixed text-ink rounded-2xl shadow-[0_8px_60px_rgba(0,0,0,0.08)] overflow-hidden flex flex-col h-full">
            <div className="px-8 py-6 border-b border-tertiary-fixed-dim bg-tertiary-fixed-dim/20 flex items-center justify-between">
              <h2 className="font-headline-lg text-headline-lg text-ink">Identified Mental Models</h2>
              <div className="flex items-center gap-3 bg-surface-container-lowest/50 px-4 py-2 rounded-full border border-outline-variant/30">
                <span className="material-symbols-outlined text-outline text-[18px]">filter_list</span>
                <span className="font-label-sm text-label-sm text-ink">Sort by: Confirmed students (desc)</span>
              </div>
            </div>

            <div className="flex flex-col divide-y divide-tertiary-fixed-dim/40 overflow-y-auto">
              {items.length === 0 && !error && (
                <p className="px-8 py-10 font-body-md text-body-md text-ink/70">
                  Nothing confirmed yet.
                </p>
              )}
              {items.map((it) => {
                const b = band(it.share);
                return (
                  <div
                    key={it.misconception_id}
                    className="px-8 py-6 hover:bg-tertiary-fixed-dim/10 transition-colors group relative flex flex-col md:flex-row gap-6 items-start md:items-center"
                  >
                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${b.bar} opacity-100 group-hover:w-2 transition-all`}></div>
                    <div className="flex-1 flex flex-col gap-2 min-w-0 pr-4">
                      <div className="flex items-center gap-3">
                        <span className={`${b.chip} ${b.text} font-label-sm text-label-sm px-2 py-1 rounded font-semibold`}>
                          {b.label}
                        </span>
                        <h4 className="font-title-md text-title-md truncate text-ink">{it.label}</h4>
                      </div>
                      <p className="font-body-md text-body-md text-ink line-clamp-2">
                        Problem type <code className="font-label-sm">{it.problem_type}</code> — {it.confirmed_count} student
                        {it.confirmed_count === 1 ? "" : "s"} confirmed this exact reasoning.
                      </p>
                    </div>
                    <div className="flex items-center gap-8 shrink-0">
                      <div className="flex flex-col items-end">
                        <span className="font-label-sm text-label-sm text-ink uppercase">Frequency</span>
                        <span className="font-headline-lg text-headline-lg text-ink">
                          {Math.round(it.share * 100)}%
                        </span>
                      </div>
                      <div className="w-24 h-2 bg-ink/10 rounded-full overflow-hidden hidden md:block">
                        <div className={`${b.bar} h-full rounded-full`} style={{ width: `${(it.share / max) * 100}%` }}></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="px-8 py-4 border-t border-tertiary-fixed-dim bg-tertiary-fixed-dim/10 flex justify-between items-center mt-auto">
              <span className="font-label-sm text-label-sm text-ink/70">
                Polling every {POLL_MS / 1000}s — no refresh needed
              </span>
              <span className="font-label-sm text-label-sm text-ink/70">
                {items.length} shown
              </span>
            </div>
          </div>
        </div>
      </div>
    </TeacherChrome>
  );
}
