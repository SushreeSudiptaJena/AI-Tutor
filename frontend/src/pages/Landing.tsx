import { Link } from "react-router-dom";
import { ArrowRight, GraduationCap, ShieldCheck, Sparkles } from "lucide-react";

/**
 * The front door. Two doors exist in this app -- students at /login, admins
 * at /admin/login -- and before this page "/" fell through to the student
 * login, leaving the admin console undiscoverable. The design language is the
 * student surface's (cream / forest green / Playfair), which is the product;
 * the admin door is deliberately quieter.
 */
export default function Landing() {
  return (
    <main className="flex min-h-screen flex-col bg-cream text-on-surface">
      {/* Top bar */}
      <nav className="flex items-center justify-between px-xl py-md">
        <span className="font-sans text-xl font-bold tracking-widest text-forest-green uppercase">
          Journey
        </span>
        <Link
          to="/login"
          className="rounded-full border border-forest-green/30 px-md py-xs text-label-md font-bold text-forest-green transition-colors hover:bg-sage-light"
        >
          Log in
        </Link>
      </nav>

      {/* Hero */}
      <section className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center gap-lg px-xl py-xl text-center">
        <Sparkles className="h-10 w-10 text-mustard" />

        <h1 className="font-serif text-5xl leading-tight text-forest-green sm:text-6xl">
          The tutor that knows<br />what you haven't learned yet.
        </h1>

        <p className="max-w-2xl text-body-lg text-on-surface-variant">
          Curriculum-aligned help that cites your own textbooks, finds the
          prerequisite you're missing, and tells your teacher exactly where the
          class is struggling — with evidence, not vibes.
        </p>

        {/* The two doors */}
        <div className="mt-md grid w-full max-w-3xl grid-cols-1 gap-md sm:grid-cols-2">
          <Link
            to="/login"
            className="group flex flex-col items-start gap-sm rounded-xl border border-forest-green/20 bg-white p-lg text-left shadow-sm transition-all hover:border-forest-green hover:shadow-md"
          >
            <span className="flex items-center gap-sm text-label-md font-bold tracking-wider text-forest-green uppercase">
              <GraduationCap className="h-5 w-5" />
              Students & teachers
            </span>
            <span className="text-body-sm text-on-surface-variant">
              Take the diagnostic, see your gaps, get lessons grounded in your
              course books. Teachers: sign in with the password your admin
              issued.
            </span>
            <span className="mt-auto flex items-center gap-xs pt-sm text-label-md font-bold text-forest-green">
              Enter
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>

          <Link
            to="/admin/login"
            className="group flex flex-col items-start gap-sm rounded-xl border border-outline-variant bg-surface-container-lowest p-lg text-left shadow-sm transition-all hover:border-on-surface-variant hover:shadow-md"
          >
            <span className="flex items-center gap-sm text-label-md font-bold tracking-wider text-on-surface-variant uppercase">
              <ShieldCheck className="h-5 w-5" />
              Admin console
            </span>
            <span className="text-body-sm text-on-surface-variant">
              Create batches, upload curriculum and materials, assign teachers,
              read the audit log.
            </span>
            <span className="mt-auto flex items-center gap-xs pt-sm text-label-md font-bold text-on-surface-variant group-hover:text-on-surface">
              Enter
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>
        </div>
      </section>

      <footer className="px-xl py-md text-center text-label-sm text-on-surface-variant">
        Every answer is evidence-checked against the approved course corpus.
      </footer>
    </main>
  );
}
