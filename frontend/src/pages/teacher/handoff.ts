/**
 * One panel handing a selection to the next.
 *
 * The teacher console has no router: `TeacherDashboard` swaps panels from a
 * single `useState`, and navigation is a delegated click on `[data-path]`.
 * That is deliberate and works fine — but it means a link cannot carry a
 * parameter, so "show me the reasoning behind THIS misconception" had nowhere
 * to put "this".
 *
 * sessionStorage rather than a module variable, because the panel that reads
 * it may mount after a full reload (switching subject calls
 * `window.location.reload()`), and a module variable does not survive that.
 *
 * **Read once, then gone.** `takeHandoff` clears the key, so arriving at the
 * panel from the sidebar shows its own default rather than silently replaying
 * a choice made minutes ago on a different screen.
 */

const KEY = "kyodo_teacher_handoff";

export function setHandoff(panel: string, value: string) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify({ panel, value }));
  } catch {
    // Private browsing, or storage disabled. The navigation still happens and
    // the target panel falls back to its default selection.
  }
}

export function takeHandoff(panel: string): string | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { panel?: string; value?: string };
    if (parsed?.panel !== panel) return null;
    sessionStorage.removeItem(KEY);
    return parsed.value ?? null;
  } catch {
    return null;
  }
}
