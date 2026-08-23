/**
 * Minimal i18n. No library — a dictionary lookup plus {placeholder} substitution.
 *
 * Adding a language: drop in `xx.json` with the same keys as en.json, add it to
 * DICTS and LANGUAGES below. Missing keys fall back to English, so a partial
 * translation degrades gracefully instead of rendering blanks.
 */

import en from "./en.json";
import hi from "./hi.json";

export type Lang = "en" | "hi";

const DICTS: Record<Lang, Record<string, string>> = { en, hi };

export const LANGUAGES: { code: Lang; label: string }[] = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
];

const STORAGE_KEY = "ai_tutor_lang";

export function getLang(): Lang {
  const saved = localStorage.getItem(STORAGE_KEY);
  return saved === "hi" || saved === "en" ? saved : "en";
}

export function setLang(lang: Lang) {
  localStorage.setItem(STORAGE_KEY, lang);
  document.documentElement.lang = lang; // screen readers use this — a11y-001
}

/**
 * t("lesson.aligned", { percent: 82})  ->  "82% syllabus aligned"
 *
 * Falls back to English, then to the key itself, so a missing string is
 * visible in the UI rather than silently blank.
 */
export function t(key: string, vars?: Record<string, string | number>): string {
  const lang = getLang();
  let s = DICTS[lang]?.[key] ?? DICTS.en[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      s = s.replaceAll(`{${k}}`, String(v));
    }
  }
  return s;
}
