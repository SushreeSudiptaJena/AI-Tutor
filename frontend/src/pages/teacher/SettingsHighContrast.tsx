/**
 * Teacher settings.
 *
 * Originally converted from
 * stitch_ascent_educator_dashboard/settings_high_contrast/settings_high_contrast.html
 * and left as the raw export, which made it the one teacher screen that
 * rendered its own <aside> and <header>. Inside TeacherDashboard those painted
 * a second, darker shell directly on top of TeacherChrome's -- which is what
 * "the navbar darkens on Settings" was. It is now wrapped in TeacherChrome
 * like every other panel, so there is exactly one sidebar and one header.
 *
 * Two things the mockup had are deliberately gone:
 *
 *   * **Account Information.** Name, role and email now live behind the
 *     top-right avatar (TeacherProfile), which is where a teacher looks for
 *     them. Duplicating them here meant two screens claiming to own the same
 *     facts -- and the mockup's copy was editable and hardcoded to
 *     "Dr. Sarah Ascent", so it also invited an edit that no endpoint accepts.
 *   * **The theme toggle.** Removed for now at the owner's request: there is
 *     no dark palette for this surface, so the switch could only mislabel the
 *     one theme that exists.
 *
 * What is left is real. Language is `PATCH /auth/me/preferences` (i18n-001) and
 * it round-trips. The mockup's two notification toggles are not here for the
 * same reason the dashboard's "Avg. Mastery" card is not: nothing stores that
 * preference, and a switch that forgets is worse than no switch.
 */
import { useEffect, useState } from "react";
import TeacherChrome from "./TeacherChrome";
import {
  cached,
  getLanguages,
  getMe,
  invalidateCache,
  updatePreferences,
  type User,
} from "@/lib/api";

function errorText(err: unknown): string {
  const detail = (err as { detail?: { message?: string } })?.detail;
  return detail?.message ?? (err as Error)?.message ?? "Something went wrong.";
}

export default function SettingsHighContrast() {
  const [me, setMe] = useState<User | null>(null);
  const [langs, setLangs] = useState<{ code: string; label: string }[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    cached("me", getMe)
      .then((u) => alive && setMe(u))
      .catch((err) => alive && setError(errorText(err)));
    getLanguages()
      .then((r) => alive && setLangs(r.items))
      .catch((err) => alive && setError(errorText(err)));
    return () => {
      alive = false;
    };
  }, []);

  async function changeLanguage(code: string) {
    setError(null);
    setSaved(false);
    setSaving(true);
    try {
      const updated = await updatePreferences(code);
      setMe(updated);
      // The header and the profile both read `me` out of the session cache;
      // leaving the stale copy there shows the old language until a reload.
      invalidateCache("me");
      setSaved(true);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <TeacherChrome active="settings">
      <header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-ink/15 pb-8">
        <div className="flex flex-col max-w-2xl">
          <span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-ink mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-orange">tune</span>
            Console preferences
          </span>
          <h1 className="font-display-lg text-display-lg text-ink m-0 leading-tight">Settings</h1>
          <p className="font-body-lg text-body-lg text-ink mt-4 max-w-[36rem]">
            How this console behaves. Your name, email and the subjects you teach live on your
            profile, behind the avatar in the top right.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        <section className="bg-card p-8 rounded-2xl border border-outline-variant shadow-[0_6px_14px_-10px_rgba(43,41,38,0.24)]">
          <h2 className="font-title-md text-title-md text-ink mb-6 pb-4 border-b border-ink/10">
            Language
          </h2>
          <p className="font-body-md text-body-md text-ink-soft mb-6">
            The language explanations are written in. The material is retrieved in English either
            way and the citations do not change — only the prose does.
          </p>

          <div className="flex items-center gap-4 flex-wrap">
            <select
              value={me?.preferred_language ?? "en"}
              disabled={saving || !me || langs.length === 0}
              onChange={(e) => changeLanguage(e.target.value)}
              aria-label="Preferred language"
              className="bg-paper border border-outline-variant rounded-lg px-4 py-2.5 font-body-md text-body-md text-ink outline-none focus:border-orange disabled:opacity-60"
            >
              {langs.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
            {saving && (
              <span className="font-label-sm text-label-sm text-ink-faint">Saving…</span>
            )}
            {saved && !saving && (
              <span className="font-label-sm text-label-sm text-orange">Saved</span>
            )}
          </div>

          {error && (
            <p role="alert" className="font-label-sm text-label-sm text-orange mt-4">
              {error}
            </p>
          )}
        </section>

        <section className="bg-card p-8 rounded-2xl border border-outline-variant shadow-[0_6px_14px_-10px_rgba(43,41,38,0.24)] flex flex-col">
          <h2 className="font-title-md text-title-md text-ink mb-6 pb-4 border-b border-ink/10">
            Your account
          </h2>
          <p className="font-body-md text-body-md text-ink-soft">
            Account details and signing out moved to your profile. Your account — including your
            password — is issued by your department admin, so there is nothing here to edit.
          </p>
          {/* TeacherDashboard delegates every [data-path] click, so this is
              the same navigation the sidebar and the avatar use. */}
          <a href="#" data-path="profile" className="btn-ghost mt-auto self-start pt-6">
            Open your profile →
          </a>
        </section>
      </div>
    </TeacherChrome>
  );
}
