/**
 * Fail the build when a class the app uses was never generated.
 *
 *   node frontend/scripts/check-utilities.mjs
 *
 * WHY THIS EXISTS
 * Tailwind v4 generates a utility only for a token declared in a build-time
 * `@theme` block. A token declared in a plain class (.admin-scope,
 * .teacher-scope) still resolves as a CSS variable, so it LOOKS fine in
 * devtools -- but `bg-inverse-surface` / `p-card-inner-padding` are never
 * emitted. There is no build error, no missing class in the DOM, and no
 * warning: the element simply has no background, or no padding.
 *
 * That has bitten this project three times:
 *   1. max-w-sm resolving to var(--spacing-sm) = 16px (text one word per line)
 *   2. w-sidebar-width vanishing when the teacher tokens were first scoped
 *   3. the whole admin + teacher palette and spacing scale, after the
 *      palette-bleed fix moved those tokens into scope classes
 *
 * A named token that a scope overrides must ALSO be declared in @theme.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

// Resolve from this file, not from cwd: npm runs it with cwd=frontend/ and a
// human runs it from the repo root.
const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "..", "src");
const DIST = join(HERE, "..", "dist", "assets");

const walk = (dir) =>
  readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });

const cssFile = readdirSync(DIST)
  .filter((f) => f.startsWith("index-") && f.endsWith(".css"))
  .map((f) => ({ f, t: statSync(join(DIST, f)).mtimeMs }))
  .sort((a, b) => b.t - a.t)[0];
if (!cssFile) {
  console.error("no built css found -- run `npm run build` first");
  process.exit(2);
}
const css = readFileSync(join(DIST, cssFile.f), "utf8");

// classes we author by hand in index.css, plus non-Tailwind hooks
const OURS = new Set(["admin-scope", "teacher-scope", "md-body", "dark", "group",
  "peer", "material-symbols-outlined", "sr-only"]);
const OURS_PREFIX = ["ns-", "role-card", "glass-card", "glow-active", "check-icon",
  "text-lg-mode", "text-xl-mode", "high-contrast"];

// only the prefixes whose value comes from a theme token
const TOKEN_CLASS =
  /^(bg|text|border|ring|fill|stroke|divide|outline|from|to|via|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|gap-x|gap-y|space-y|space-x|w|h|min-w|min-h|max-w|max-h|font|rounded|shadow)-([a-z][a-z0-9-]*)$/;

const CLASS_ATTR = /className=(?:"([^"]*)"|\{`([^`]*)`\}|\{"([^"]*)"\})/gs;

const used = new Map();
for (const path of walk(SRC).filter((p) => p.endsWith(".tsx"))) {
  const text = readFileSync(path, "utf8");
  for (const m of text.matchAll(CLASS_ATTR)) {
    const blob = (m[1] ?? m[2] ?? m[3] ?? "").replace(/\$\{[^}]*\}/g, " ");
    for (const raw of blob.split(/\s+/)) {
      if (!raw || raw.includes("[") || raw.includes("(")) continue; // arbitrary values are literal
      const base = raw.split(":").pop().replace(/^-/, "").split("/")[0];
      if (OURS.has(base) || OURS_PREFIX.some((p) => base.startsWith(p))) continue;
      if (!TOKEN_CLASS.test(base)) continue;
      if (!used.has(base)) used.set(base, new Set());
      used.get(base).add(path.replace(/\\/g, "/").slice(SRC.length + 1));
    }
  }
}

// A class counts as generated if it appears as a selector in ANY form: bare,
// with an escaped variant (.md\:p-x), or with an opacity modifier (.bg-x\/20).
const present = (cls) => {
  const esc = cls.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  // The class may appear bare (.p-x), behind an escaped variant
  // (.md\:p-x, .hover\:bg-x), or with an opacity modifier (.bg-x\/20), and may
  // be followed by a pseudo-class. Anchor on "." or an escaped colon so a
  // variant-only usage is not reported as missing.
  return new RegExp("(?:\\.|\\\\:)" + esc + "(?=[,{>:\\s\\\\])").test(css);
};

const missing = [...used.entries()].filter(([cls]) => !present(cls));

if (missing.length === 0) {
  console.log(`utilities ok: ${used.size} token classes, all generated (${cssFile.f})`);
  process.exit(0);
}

console.error(`\n${missing.length} class(es) used but NEVER GENERATED -- they do nothing:\n`);
for (const [cls, files] of missing.sort()) {
  console.error(`  ${cls.padEnd(30)} <- ${[...files].slice(0, 3).join(", ")}`);
}
console.error(
  "\nDeclare the token in the @theme block of src/index.css (a scope class is\n" +
  "not enough -- see the header of this file), or use an explicit value.\n",
);
process.exit(1);
