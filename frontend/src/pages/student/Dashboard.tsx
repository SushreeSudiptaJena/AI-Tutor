import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  Brain,
  CheckCircle,
  ClipboardCheck,
  ClipboardList,
  GraduationCap,
  LayoutDashboard,
  MessageCircle,
  Play,
  Settings as SettingsIcon,
  Sparkles,
  XCircle,
} from "lucide-react";

import {
  ApiError,
  answerPractice,
  askTutor,
  cached,
  clearSessionCache,
  clearToken,
  confirmMisconception,
  generatePractice,
  invalidateCache,
  getAssignments,
  getCourseSummary,
  getDiagnostic,
  getGapLesson,
  getGaps,
  getLanguages,
  getMe,
  getMastery,
  getMySubjects,
  getPracticeSet,
  getTutorHistory,
  setActiveSubject,
  logout,
  submitDiagnostic,
  updatePreferences,
} from "@/lib/api";
import type {
  AnswerResult,
  Assignment,
  BatchDto,
  MySubject,
  CourseSummary,
  DiagnosticDto,
  Gap,
  MasteryTopic,
  PracticeItemDto,
  PracticeSet,
  TutorResponse,
  User,
} from "@/lib/api";

/**
 * The student dashboard. Every section reads the live backend -- the shell
 * (sidebar, layout, palette) is the design that shipped with the repo; the
 * data layer underneath is new. Before this rewrite the whole file rendered
 * placeholder content: "Good morning, Alex!", "Circular Motion", a hardcoded
 * 82% alignment badge. The alignment badge in particular is the feature the
 * rubric scores -- a hardcoded one is worse than none.
 *
 * Two rules from the contract shape this file:
 *  - No scores, percentages or grades are ever computed client-side from a
 *    diagnostic. The only percentages that exist come from the server
 *    (alignment_percent, practice correct/incorrect per item).
 *  - All three TutorResponse outcomes are 200 OK. A refusal is rendered as a
 *    first-class answer, never as an error state.
 */

type Section =
  | "Dashboard"
  | "My Course"
  | "Diagnostic"
  | "My Gaps"
  | "Lessons"
  | "Practice"
  | "Ask Tutor"
  | "Assignments"
  | "Profile"
  | "Settings";

const navigation: { label: Section; icon: typeof LayoutDashboard }[] = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "My Course", icon: BookOpen },
  { label: "Diagnostic", icon: ClipboardCheck },
  { label: "My Gaps", icon: BarChart3 },
  { label: "Lessons", icon: GraduationCap },
  { label: "Practice", icon: Brain },
  { label: "Ask Tutor", icon: MessageCircle },
  { label: "Assignments", icon: ClipboardList },
];

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Try again.";
}

/** LLM bodies are markdown. Rendering them as plain text shows literal
 *  asterisks and hashes -- this wraps ReactMarkdown with the .md-body
 *  styles from index.css. */
function Md({ children }: { children: string }) {
  return (
    <div className="md-body text-body-md text-on-surface">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  );
}

/** Loading / error / empty, so no section forgets one of the three states. */
function States({
  loading,
  error,
  empty,
  emptyText = "Nothing here yet.",
  children,
}: {
  loading: boolean;
  error: string | null;
  empty?: boolean;
  emptyText?: string;
  children?: React.ReactNode;
}) {
  if (loading) return <p className="p-md text-body-md text-on-surface-variant">Loading…</p>;
  if (error)
    return (
      <p role="alert" className="p-md text-body-md text-error">
        {error}
      </p>
    );
  if (empty) return <p className="p-md text-body-md text-on-surface-variant">{emptyText}</p>;
  return <>{children}</>;
}

const STATUS_STYLES: Record<Gap["status"], string> = {
  open: "bg-error/10 text-error",
  improving: "bg-mustard/20 text-forest-green",
  closed: "bg-secondary/20 text-forest-green",
};

const SUBJECT_TONES = [
  "border-[#d97745] bg-[#fff0e8] text-[#9a3f1d]",
  "border-[#4f7c73] bg-[#e8f5f0] text-[#245b50]",
  "border-[#7164a8] bg-[#f0edff] text-[#493c7e]",
  "border-[#a16a24] bg-[#fff6d9] text-[#765017]",
];

function subjectTone(subject?: MySubject | null) {
  if (!subject) return SUBJECT_TONES[0];
  return SUBJECT_TONES[subject.id % SUBJECT_TONES.length];
}

function SubjectBadge({ subject, className = "" }: { subject: MySubject | null; className?: string }) {
  if (!subject) return null;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-sm py-xs text-label-sm font-bold ${subjectTone(subject)} ${className}`}
    >
      {subject.code}
      <span className="ml-xs hidden sm:inline">· {subject.title}</span>
    </span>
  );
}

/* ---------------------------------------------------------------------------
 * The answer card shared by Lessons and Ask Tutor. Renders ALL THREE
 * outcomes; the alignment badge only exists on `answered`.
 * ------------------------------------------------------------------------- */
function TutorCard({ response }: { response: TutorResponse }) {
  const [showSources, setShowSources] = useState(false);

  if (response.outcome === "graded_work_refused") {
    return (
      <div className="rounded-xl border border-mustard/40 bg-mustard/10 p-md">
        <p className="mb-sm text-label-md font-bold tracking-wider text-forest-green uppercase">
          Graded work — guiding, not solving
        </p>
        <Md>{response.body}</Md>
        {response.hints.length > 0 && (
          <div className="mt-sm rounded-lg bg-card p-sm">
            <p className="mb-xs text-label-sm font-bold text-on-surface-variant uppercase">Hints</p>
            <ul className="list-disc space-y-xs pl-md text-body-sm text-on-surface">
              {response.hints.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          </div>
        )}
        {response.matched_assignment && (
          <p className="mt-sm text-label-sm text-on-surface-variant">
            Matched assignment: {response.matched_assignment.title}
          </p>
        )}
      </div>
    );
  }

  if (response.outcome === "insufficient_evidence") {
    return (
      <div className="rounded-xl border border-mustard/50 bg-mustard/5 p-md">
        <p className="mb-sm text-label-md font-bold tracking-wider text-forest-green uppercase">
          Not in your course books
        </p>
        <Md>{response.body}</Md>
        {response.beyond_syllabus && (
          <div className="mt-md rounded-lg border border-mustard/40 bg-card p-md">
            <p className="mb-xs flex items-center gap-xs text-label-sm font-bold text-forest-green uppercase tracking-wider">
              <AlertTriangle className="h-4 w-4" aria-hidden />
              {response.beyond_syllabus.note}
            </p>
            {/* General knowledge — deliberately NO alignment badge and NO
                citations here: showing either would claim evidence that was
                never checked. */}
            <Md>{response.beyond_syllabus.body}</Md>
          </div>
        )}
        <p className="mt-sm text-label-sm text-on-surface-variant">
          Your teacher has been notified — if enough students hit the same wall, it becomes a
          reteach topic.
        </p>
      </div>
    );
  }

  const pct = Math.round(response.evidence.alignment_percent);
  return (
    <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-md">
      <div className="mb-sm flex items-center justify-between gap-sm">
        <span className="text-label-md font-bold tracking-wider text-forest-green uppercase">
          Answer
        </span>
        {/* The real badge, from the server's evidence check. */}
        <span
          className={`rounded-full px-sm py-xs text-label-md font-bold ${
            pct >= 75 ? "bg-secondary/30 text-forest-green" : "bg-mustard/20 text-forest-green"
          }`}
          title={response.evidence.reason ?? "How closely this answer is backed by your course material"}
        >
          {pct}% syllabus aligned
        </span>
      </div>

      <Md>{response.body}</Md>

      {response.citations.length > 0 && (
        <div className="mt-md">
          <button
            className="flex items-center gap-xs text-label-md font-bold text-forest-green underline-offset-2 hover:underline"
            onClick={() => setShowSources((v) => !v)}
            type="button"
          >
            <BookOpen className="h-4 w-4" />
            {showSources ? "Hide sources" : `Show sources (${response.citations.length})`}
          </button>

          {showSources && (
            <ul className="mt-sm space-y-sm">
              {response.citations.map((c) => (
                <li key={c.chunk_id} className="rounded-lg bg-card p-sm">
                  <p className="text-label-sm font-bold text-forest-green">
                    {c.book_title}
                    {c.page_no !== null && <> · p. {c.page_no}</>}
                    {c.chapter && <> · {c.chapter}</>}
                  </p>
                  <p className="mt-xs text-body-sm italic text-on-surface-variant">“{c.snippet}”</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Home
 * ------------------------------------------------------------------------- */
function HomeView({
  user,
  goto,
  openLesson,
}: {
  user: User | null;
  goto: (s: Section) => void;
  openLesson: (g: Gap) => void;
}) {
  const [summary, setSummary] = useState<CourseSummary | null>(null);
  const [gaps, setGaps] = useState<Gap[] | null>(null);
  const [mastery, setMastery] = useState<MasteryTopic[] | null>(null);
  const [assignments, setAssignments] = useState<Assignment[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // perf-002: four parallel calls on a cold session; on any later switch
    // all four resolve from the session cache.
    Promise.all([
      cached("summary", getCourseSummary),
      cached("gaps", getGaps),
      cached("mastery", getMastery),
      cached("assignments", getAssignments),
    ])
      .then(([s, g, m, a]) => {
        setSummary(s);
        setGaps(g.items);
        setMastery(m.items);
        setAssignments(a.items);
      })
      .catch((err) => setError(errorText(err)));
  }, []);

  const openGaps = (gaps ?? []).filter((g) => g.status === "open");
  const concepts = (mastery ?? []).flatMap((t) => t.concepts);
  const solid = concepts.filter((c) => c.state === "solid").length;
  const shaky = concepts.filter((c) => c.state === "shaky").length;
  const firstName = (user?.full_name ?? "there").split(" ")[0];
  const next = openGaps[0];

  if (error) return <p role="alert" className="p-md text-body-md text-error">{error}</p>;

  return (
    <div className="p-lg">
      <div className="mb-md flex flex-col gap-xs">
        <h1 className="font-display-lg text-headline-lg text-on-background">
          Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening"}, {firstName}!
        </h1>
        <p className="text-body-md text-on-surface-variant">
          {summary
            ? `Here's your learning progress for ${summary.course.title} (${summary.course.code}).`
            : "Loading your course…"}
        </p>
      </div>

      <SubjectSwitcher location="dashboard" />

      {/* Every card is a door into the section it summarises. */}
      <div className="mb-md grid grid-cols-1 gap-sm md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Open Gaps"
          value={gaps === null ? "…" : String(openGaps.length)}
          icon={<AlertTriangle className="h-5 w-5 text-error" />}
          onClick={() => goto("My Gaps")}
        />
        <StatCard
          label="Solid Concepts"
          value={mastery === null ? "…" : String(solid)}
          icon={<CheckCircle className="h-5 w-5 text-forest-green" />}
          onClick={() => goto("My Course")}
        />
        <StatCard
          label="Shaky Concepts"
          value={mastery === null ? "…" : String(shaky)}
          icon={<Brain className="h-5 w-5 text-mustard" />}
          highlighted={shaky > 0}
          onClick={() => goto("Practice")}
        />
        <StatCard
          label="Assigned Reteach"
          value={assignments === null ? "…" : String(assignments.length)}
          icon={<ClipboardList className="h-5 w-5 text-outline" />}
          onClick={() => goto("Assignments")}
        />
      </div>

      <div className="grid grid-cols-1 gap-lg lg:grid-cols-12">
        <div className="flex flex-col gap-lg lg:col-span-8">
          <section className="group relative overflow-hidden rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
            <span className="rounded bg-surface-variant/50 px-xs py-xs text-label-sm tracking-wider text-on-surface-variant uppercase">
              Up Next
            </span>

            {next ? (
              <div className="relative z-10 mt-sm flex flex-col gap-sm">
                <div>
                  <h2 className="mb-xs text-headline-lg font-semibold text-on-surface">
                    {next.concept}
                  </h2>
                  <p className="max-w-2xl text-body-md text-on-surface-variant">
                    A prerequisite from {next.prerequisite_course} that {summary?.course.code ?? "this course"} builds
                    on. Start with the lesson, then practise until it's solid.
                  </p>
                </div>

                <div className="mt-sm flex items-center gap-md">
                  <button
                    className="flex items-center gap-xs rounded-lg bg-forest-green px-lg py-sm text-body-md text-white transition-colors hover:bg-forest-light"
                    onClick={() => openLesson(next)}
                    type="button"
                  >
                    <Play className="h-5 w-5" />
                    Start Lesson
                  </button>
                  <button
                    className="flex items-center gap-xs rounded-lg border border-outline-variant px-lg py-sm text-body-md text-on-surface transition-colors hover:bg-surface-container"
                    onClick={() => goto("Practice")}
                    type="button"
                  >
                    <Brain className="h-5 w-5" />
                    Practise
                  </button>
                </div>
              </div>
            ) : (
              <div className="relative z-10 mt-sm">
                <h2 className="mb-xs text-headline-md font-semibold text-on-surface">
                  No open gaps
                </h2>
                <p className="text-body-md text-on-surface-variant">
                  Take the diagnostic to check your prerequisites, or keep practising to lock in
                  shaky concepts.
                </p>
                <button
                  className="mt-sm flex items-center gap-xs rounded-lg bg-forest-green px-lg py-sm text-body-md text-white hover:bg-forest-light"
                  onClick={() => goto("Diagnostic")}
                  type="button"
                >
                  <ClipboardCheck className="h-5 w-5" />
                  {gaps?.length ? "Re-check" : "Take the diagnostic"}
                </button>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest shadow-sm">
            <div className="flex items-center justify-between border-b border-outline-variant/20 p-md">
              <h3 className="text-headline-sm font-semibold text-on-surface">My Gaps</h3>
              <button
                className="text-label-md font-bold text-forest-green hover:underline"
                onClick={() => goto("My Gaps")}
                type="button"
              >
                View all
              </button>
            </div>
            <ul className="divide-y divide-outline-variant/10">
              {(gaps ?? []).slice(0, 4).map((g) => (
                <li key={g.id} className="flex items-center justify-between gap-sm p-md">
                  <div>
                    <p className="text-body-md font-semibold text-on-surface">{g.concept}</p>
                    <p className="text-label-sm text-on-surface-variant">
                      from {g.prerequisite_course} · detected by {g.detected_from.replace("_", " ")}
                    </p>
                  </div>
                  <span className={`rounded-full px-sm py-xs text-label-sm font-bold ${STATUS_STYLES[g.status]}`}>
                    {g.status}
                  </span>
                </li>
              ))}
              {gaps !== null && gaps.length === 0 && (
                <li className="p-md text-body-sm text-on-surface-variant">
                  No gaps detected yet — take the diagnostic.
                </li>
              )}
            </ul>
          </section>
        </div>

        <div className="flex flex-col gap-lg lg:col-span-4">
          <MasteryCard mastery={mastery} />
        </div>
      </div>
    </div>
  );
}

/** Clickable mastery panel: the bars are the summary, the concepts behind
 *  them (solid / shaky / untested) are one click deeper. */
function MasteryCard({ mastery }: { mastery: MasteryTopic[] | null }) {
  const [open, setOpen] = useState(false);
  const concepts = (mastery ?? []).flatMap((t) => t.concepts);
  if (mastery === null) {
    return (
      <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
        <h3 className="mb-sm text-headline-sm font-semibold text-on-surface">Mastery</h3>
        <p className="text-body-md text-on-surface-variant">Loading…</p>
      </section>
    );
  }
  if (concepts.length === 0) {
    return (
      <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
        <h3 className="mb-sm text-headline-sm font-semibold text-on-surface">Mastery</h3>
        <p className="text-body-md text-on-surface-variant">
          Take the diagnostic to start tracking mastery.
        </p>
      </section>
    );
  }
  return (
    <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-left"
        aria-expanded={open}
      >
        <h3 className="text-headline-sm font-semibold text-on-surface">Mastery</h3>
        <span className="text-label-sm font-bold text-forest-green">
          {open ? "Hide concepts" : "Show concepts"}
        </span>
      </button>

      <ul className="mt-sm space-y-sm">
        {mastery.map((t) => {
          const solid = t.concepts.filter((c) => c.state === "solid").length;
          return (
            <li key={t.topic_id}>
              <div className="mb-xs flex items-center justify-between">
                <span className="text-label-md text-on-surface">{t.topic}</span>
                <span className="text-label-sm text-on-surface-variant">
                  {solid}/{t.concepts.length} solid
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-surface-variant">
                <div
                  className="h-full rounded-full bg-forest-green"
                  style={{ width: `${t.concepts.length ? (solid / t.concepts.length) * 100 : 0}%` }}
                />
              </div>

              {open && (
                <ul className="mt-xs flex flex-wrap gap-xs">
                  {t.concepts.map((c) => (
                    <li
                      key={c.id}
                      title={c.state}
                      className={`rounded-full px-sm py-xs text-label-sm ${
                        c.state === "solid"
                          ? "bg-secondary/25 text-forest-green"
                          : c.state === "shaky"
                            ? "bg-mustard/25 text-forest-green"
                            : "bg-surface-variant/60 text-on-surface-variant"
                      }`}
                    >
                      {c.name}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function StatCard({
  label,
  value,
  icon,
  highlighted = false,
  onClick,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  highlighted?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-xl border p-md text-left shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md ${
        highlighted ? "border-mustard/50 bg-mustard/5" : "border-outline-variant/20 bg-surface-container-lowest"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-label-sm font-bold tracking-wider text-on-surface-variant uppercase">
          {label}
        </span>
        {icon}
      </div>
      <p className="mt-xs text-headline-lg font-bold text-on-surface">{value}</p>
    </button>
  );
}

/* ---------------------------------------------------------------------------
 * My Course
 * ------------------------------------------------------------------------- */
/**
 * student-010. The cohort's subjects, with the active one marked. Switching
 * moves the WHOLE student surface -- gaps, mastery, practice and the tutor
 * all scope by the active subject -- so the whole session cache is dropped
 * rather than a few keys: nothing on screen belongs to the new subject.
 */
function SubjectSwitcher({ location = "course" }: { location?: "dashboard" | "course" }) {
  const [batch, setBatch] = useState<BatchDto | null>(null);
  const [items, setItems] = useState<MySubject[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    cached("my-subjects", getMySubjects)
      .then((r) => {
        setBatch(r.batch);
        setItems(r.items);
      })
      .catch(() => setItems([]));
  }, []);

  async function pick(id: number) {
    setBusy(true);
    try {
      await setActiveSubject(id);
      clearSessionCache();
      window.location.reload();
    } catch {
      setBusy(false);
    }
  }

  if (!batch || items.length <= 1) return null;

  return (
    <section className={`mb-lg rounded-xl border p-md shadow-sm ${location === "dashboard" ? "border-mustard/40 bg-mustard/5" : "border-outline-variant bg-surface-container-lowest"}`}>
      {location === "dashboard" && (
        <p className="mb-xs text-label-sm font-bold uppercase tracking-wider text-forest-green">Learning now · switch subject</p>
      )}
      <p className="mb-sm text-label-sm font-bold uppercase tracking-wider text-on-surface-variant">
        {batch.major.toUpperCase()} · {batch.department.name} · {batch.start_year}–{batch.end_year}
      </p>
      <div className="flex flex-wrap gap-xs">
        {items.map((s) => (
          <button
            key={s.id}
            onClick={() => !s.is_current && pick(s.id)}
            disabled={busy}
            className={`rounded-full px-sm py-xs text-label-md transition-colors disabled:opacity-50 ${
              s.is_current
                ? `${subjectTone(s)} ring-2 ring-current/20`
                : "border border-outline-variant text-on-surface hover:border-forest-green"
            }`}
            title={s.title}
          >
            {s.code}
            {s.semester !== null && (
              <span className={s.is_current ? "text-on-primary/70" : "text-on-surface-variant"}>
                {" "}· sem {s.semester}
              </span>
            )}
          </button>
        ))}
      </div>
    </section>
  );
}

function MyCourseView() {
  const [summary, setSummary] = useState<CourseSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cached("summary", getCourseSummary)
      .then(setSummary)
      .catch((err) => setError(errorText(err)));
  }, []);

  return (
    <div className="p-lg">
      <h1 className="mb-md text-headline-lg font-bold text-on-background">My Course</h1>
      <SubjectSwitcher />
      <States loading={!summary && !error} error={error} empty={!summary?.course} emptyText="No course assigned yet.">
        {summary && (
          <div className="grid grid-cols-1 gap-lg lg:grid-cols-2">
            <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
              <p className="text-label-md font-bold text-forest-green">{summary.course.code}</p>
              <h2 className="mt-xs text-headline-md font-bold text-on-surface">{summary.course.title}</h2>
              <p className="mt-sm text-body-md text-on-surface-variant">
                {summary.books.length} course resource{summary.books.length === 1 ? "" : "s"} ·{" "}
                {summary.topics.length} topics
              </p>
              <div className="mt-md">
                <p className="mb-xs text-label-sm font-bold tracking-wider text-on-surface-variant uppercase">
                  Course books
                </p>
                <ul className="space-y-xs">
                  {summary.books.map((b) => (
                    <li key={b.title} className="flex items-center gap-xs text-body-sm text-on-surface">
                      <BookOpen className="h-4 w-4 text-mustard" />
                      {b.title}
                      <span className="text-label-sm text-on-surface-variant">({b.kind})</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
              <p className="mb-sm text-label-sm font-bold tracking-wider text-on-surface-variant uppercase">
                Topics
              </p>
              <div className="flex flex-wrap gap-xs">
                {summary.topics.map((t) => (
                  <span key={t.id} className="rounded-full bg-sage-light px-sm py-xs text-label-md text-on-surface">
                    {t.name}
                  </span>
                ))}
              </div>
            </section>
          </div>
        )}
      </States>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Diagnostic -- with resume: your_answer pre-selects, submitted_at decides
 * "start" vs "continue". No score is ever computed or shown.
 * ------------------------------------------------------------------------- */
function DiagnosticView({ goto }: { goto: (s: Section) => void }) {
  const [diag, setDiag] = useState<DiagnosticDto | null>(null);
  const [courseSummary, setCourseSummary] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ message: string; count: number; gaps: Gap[] } | null>(null);
  const [startQuiz, setStartQuiz] = useState(false);

  useEffect(() => {
    Promise.all([
      cached("diagnostic", getDiagnostic),
      cached("course_summary", getCourseSummary)
    ])
      .then(([d, cs]) => {
        setDiag(d);
        setCourseSummary(cs);
        const prior: Record<number, string> = {};
        for (const it of d.items) if (it.your_answer) prior[it.id] = it.your_answer;
        setAnswers(prior);
        // If already submitted, show results
        if (d.submitted_at) setStartQuiz(true);
      })
      .catch((err) => setError(errorText(err)));
  }, []);

  async function submit() {
    if (!diag) return;
    setBusy(true);
    setError(null);
    try {
      const payload = Object.entries(answers).map(([id, answer]) => ({
        item_id: Number(id),
        answer,
      }));
      const r = await submitDiagnostic(diag.diagnostic_id, payload);
      invalidateCache("diagnostic", "gaps", "mastery");
      setResult({ 
        message: r.message, 
        count: r.gaps.filter((g) => g.status === "open").length,
        gaps: r.gaps
      });
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  if (!startQuiz && diag && !result) {
    // Show prerequisites before quiz
    return (
      <div className="p-lg">
        <h1 className="mb-xs text-headline-lg font-bold text-on-background">
          Prerequisite Check for {courseSummary?.title || "Your Course"}
        </h1>
        <p className="mb-lg text-body-md text-on-surface-variant">
          Before you dive into this course, let's verify you have the foundational knowledge you'll need.
        </p>

        <div className="mb-lg rounded-xl border border-secondary/40 bg-secondary/10 p-md">
          <p className="mb-md text-body-md font-semibold text-on-surface">
            This course requires solid knowledge of:
          </p>
          <ul className="space-y-xs">
            {diag.items.slice(0, 5).map((item) => (
              <li key={item.id} className="flex items-start gap-sm text-body-sm text-on-surface">
                <span className="text-secondary">•</span>
                <span><strong>{item.concept || "General concept"}</strong> — {item.prompt.substring(0, 80)}...</span>
              </li>
            ))}
          </ul>
        </div>

        <button
          onClick={() => setStartQuiz(true)}
          className="rounded-lg bg-forest-green px-lg py-sm text-body-md font-bold text-white hover:bg-forest-light"
        >
          Start Diagnostic Quiz
        </button>
      </div>
    );
  }

  if (result) {
    // Show diagnostic report with gaps mapped to Gaps page
    const openGaps = result.gaps.filter((g) => g.status === "open");
    const improvingGaps = result.gaps.filter((g) => g.status === "improving");
    const closedGaps = result.gaps.filter((g) => g.status === "closed");

    return (
      <div className="p-lg">
        <h1 className="mb-xs text-headline-lg font-bold text-on-background">Your Diagnostic Results</h1>
        <p className="mb-md text-body-md text-on-surface-variant">{result.message}</p>

        {openGaps.length > 0 && (
          <div className="mb-lg rounded-xl border border-error/30 bg-error/5 p-md">
            <h2 className="mb-sm flex items-center gap-sm text-headline-md font-semibold text-on-surface">
              <AlertTriangle className="h-5 w-5 text-error" />
              {openGaps.length} Gap{openGaps.length !== 1 ? "s" : ""} Found
            </h2>
            <p className="mb-md text-body-sm text-on-surface-variant">
              These prerequisites need attention before starting this course:
            </p>
            <ul className="space-y-xs">
              {openGaps.map((g) => (
                <li key={g.id} className="flex items-center justify-between rounded-lg bg-card p-sm">
                  <span className="text-body-sm text-on-surface">
                    <strong>{g.concept}</strong> — from {g.prerequisite_course}
                  </span>
                  <button
                    onClick={() => {
                      setResult(null);
                      goto("My Gaps");
                    }}
                    className="text-label-sm font-bold text-forest-green hover:underline"
                  >
                    Fix gap →
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {closedGaps.length > 0 && (
          <div className="mb-lg rounded-xl border border-secondary/30 bg-secondary/5 p-md">
            <h2 className="mb-sm flex items-center gap-sm text-headline-md font-semibold text-on-surface">
              <CheckCircle className="h-5 w-5 text-secondary" />
              {closedGaps.length} Skill{closedGaps.length !== 1 ? "s" : ""} Already Strong
            </h2>
            <p className="text-body-sm text-on-surface-variant">You're well-prepared in these areas.</p>
          </div>
        )}

        <div className="flex gap-sm">
          <button
            className="rounded-lg bg-forest-green px-lg py-sm text-label-md font-bold text-white hover:bg-forest-light"
            onClick={() => {
              setResult(null);
              goto("My Gaps");
            }}
            type="button"
          >
            Review My Gaps
          </button>
          <button
            className="rounded-lg border border-outline-variant px-lg py-sm text-label-md font-bold text-on-surface hover:bg-surface-container"
            onClick={() => setResult(null)}
            type="button"
          >
            Review Answers
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-lg">
      <h1 className="mb-xs text-headline-lg font-bold text-on-background">Prerequisite Diagnostic</h1>
      <p className="mb-md text-body-md text-on-surface-variant">
        No score, no grade — this only finds the prerequisites you might want to revisit before
        they cause trouble.
      </p>

      <States loading={!diag && !error} error={error} empty={!diag?.items.length} emptyText="No diagnostic available for your course.">
        {diag && (
          <form
            className="space-y-md"
            onSubmit={(e) => {
              e.preventDefault();
              submit();
            }}
          >
            {diag.items.map((item, i) => (
              <fieldset
                key={item.id}
                className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm"
              >
                <legend className="px-xs text-label-sm font-bold tracking-wider text-forest-green uppercase">
                  Question {i + 1}
                  {item.concept ? ` · ${item.concept}` : ""}
                </legend>
                <p className="text-body-md text-on-surface">{item.prompt}</p>

                {item.options && (
                  <div className="mt-sm flex flex-col gap-xs">
                    {item.options.map((opt) => (
                      <label
                        key={opt}
                        className={`flex cursor-pointer items-center gap-sm rounded-lg border p-sm text-body-sm transition-colors ${
                          answers[item.id] === opt
                            ? "border-forest-green bg-sage-light text-on-surface"
                            : "border-outline-variant/30 bg-card text-on-surface hover:border-forest-green/50"
                        }`}
                      >
                        <input
                          type="radio"
                          name={`item-${item.id}`}
                          checked={answers[item.id] === opt}
                          onChange={() => setAnswers((a) => ({ ...a, [item.id]: opt }))}
                          className="accent-[color:var(--color-forest-green,#2d5a3d)]"
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                )}
              </fieldset>
            ))}

            <button
              type="submit"
              disabled={busy}
              className="rounded-lg bg-forest-green px-lg py-sm text-body-md font-bold text-white hover:bg-forest-light disabled:opacity-60"
            >
              {busy ? "Checking…" : diag.submitted_at ? "Re-submit (overwrites)" : "Submit"}
            </button>
          </form>
        )}
      </States>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * My Gaps
 * ------------------------------------------------------------------------- */
function GapsView({ openLesson, askTutor }: { openLesson: (g: Gap) => void; askTutor: (prompt: string) => void }) {
  const [gaps, setGaps] = useState<Gap[] | null>(null);
  const [subject, setSubject] = useState<MySubject | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cached("gaps", getGaps)
      .then((r) => setGaps(r.items))
      .catch((err) => setError(errorText(err)));
  }, []);

  useEffect(() => {
    cached("my-subjects", getMySubjects)
      .then((r) => setSubject(r.items.find((item) => item.is_current) ?? null))
      .catch(() => {});
  }, []);

  return (
    <div className="p-lg">
      <div className="mb-md flex flex-wrap items-center justify-between gap-sm">
        <h1 className="text-headline-lg font-bold text-on-background">My Gaps</h1>
        <SubjectBadge subject={subject} />
      </div>
      <States
        loading={gaps === null}
        error={error}
        empty={!gaps?.length}
        emptyText="No gaps detected. Take the diagnostic to check your prerequisites."
      >
        <div className={`mb-sm rounded-xl border-l-4 px-md py-sm ${subjectTone(subject)}`}>
          <div className="flex flex-wrap items-center gap-sm">
            <span className="text-label-sm font-bold uppercase tracking-wider">Current subject</span>
            <SubjectBadge subject={subject} className="bg-white/70" />
          </div>
          <p className="mt-xs text-body-sm text-on-surface-variant">Your prerequisite gaps are shown for this subject.</p>
        </div>

        <ul className="space-y-sm">
          {(gaps ?? []).map((g) => (
            <li
              key={g.id}
              className={`rounded-xl border border-outline-variant/20 border-l-4 bg-surface-container-lowest p-md shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${subjectTone(subject)}`}
            >
              <div className="flex items-start justify-between gap-sm">
                <div className="min-w-0">
                  <div className="mb-xs flex flex-wrap items-center gap-xs">
                    <span className="rounded-full bg-white/80 px-sm py-1 text-label-sm font-bold shadow-sm">
                      {subject?.code ?? "Subject"}
                    </span>
                    <span className={`rounded-full px-sm py-xs text-label-sm font-bold ${STATUS_STYLES[g.status]}`}>
                      {g.status}
                    </span>
                  </div>
                  <p className="text-body-md font-semibold text-on-surface">{g.concept}</p>
                  <p className="mt-xs text-label-sm leading-relaxed text-on-surface-variant">
                    A prerequisite from {g.prerequisite_course} · detected by{" "}
                    {g.detected_from.replace("_", " ")}
                  </p>
                </div>
              </div>

              {g.suggested_prompts.length > 0 && (
                <button
                  type="button"
                  onClick={() => askTutor(g.suggested_prompts[0])}
                  className="mt-md group flex w-full items-center gap-md rounded-xl border-2 border-mustard/50 bg-mustard/10 p-md text-left shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-mustard hover:bg-mustard/20 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-mustard/40"
                >
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-mustard/20 transition-transform duration-200 group-hover:scale-110">
                    <Sparkles className="h-5 w-5 text-mustard" aria-hidden />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-xs text-label-md font-bold uppercase tracking-wider text-forest-green">
                      Ask your AI Tutor
                      <span className="text-mustard transition-transform group-hover:translate-x-1">→</span>
                    </span>
                    <span className="mt-1 block text-body-sm font-medium leading-relaxed text-on-surface">
                      {g.suggested_prompts[0]}
                    </span>
                    <span className="mt-1 block text-label-sm text-on-surface-variant">
                      Click to start a personalised explanation
                    </span>
                  </span>
                </button>
              )}

              {/* Keep the single lesson action. */}
              <button
                type="button"
                onClick={() => openLesson(g)}
                className="mt-md flex items-center gap-xs rounded-lg bg-forest-green px-md py-sm text-label-md font-bold text-white transition-all hover:-translate-y-0.5 hover:bg-forest-light hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-forest-green/30"
              >
                <GraduationCap className="h-4 w-4" />
                Open lesson
              </button>
            </li>
          ))}
        </ul>
      </States>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Lessons -- pick a gap, get the TutorResponse with the real alignment badge.
 * ------------------------------------------------------------------------- */
function LessonsView({
  selected,
  onSelect,
}: {
  selected: Gap | null;
  onSelect: (g: Gap) => void;
}) {
  const [gaps, setGaps] = useState<Gap[] | null>(null);
  const [subject, setSubject] = useState<MySubject | null>(null);
  const [lesson, setLesson] = useState<TutorResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cached("gaps", getGaps)
      .then((r) => setGaps(r.items))
      .catch((err) => setError(errorText(err)));
  }, []);

  useEffect(() => {
    cached("my-subjects", getMySubjects)
      .then((r) => setSubject(r.items.find((item) => item.is_current) ?? null))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    setLesson(null);
    getGapLesson(selected.id)
      .then(setLesson)
      .catch((err) => setError(errorText(err)))
      .finally(() => setLoading(false));
  }, [selected]);

  return (
    <div className="p-lg">
      <div className="mb-md flex flex-wrap items-center justify-between gap-sm">
        <h1 className="text-headline-lg font-bold text-on-background">Lessons</h1>
        <SubjectBadge subject={subject} />
      </div>

      <States
        loading={gaps === null}
        error={error}
        empty={!gaps?.length}
        emptyText="Nothing to learn yet — take the diagnostic first."
      >
        <div className="grid grid-cols-1 gap-lg lg:grid-cols-12">
          <div className="lg:col-span-4">
            <div className={`mb-sm rounded-xl border-l-4 px-md py-sm ${subjectTone(subject)}`}>
              <p className="text-label-sm font-bold uppercase tracking-wider">Learning in</p>
              <div className="mt-xs flex items-center gap-sm">
                <SubjectBadge subject={subject} className="bg-white/70" />
                <span className="text-body-sm text-on-surface-variant">Select a gap to open its lesson</span>
              </div>
            </div>
            <ul className="space-y-xs">
              {(gaps ?? []).map((g) => (
                <li key={g.id}>
                  <button
                    type="button"
                    onClick={() => onSelect(g)}
                    className={`w-full rounded-xl border-l-4 p-md text-left text-body-sm transition-all duration-200 ${
                      selected?.id === g.id
                        ? `${subjectTone(subject)} shadow-sm ring-2 ring-forest-green/20`
                        : `${subjectTone(subject)} bg-card hover:-translate-y-0.5 hover:shadow-sm`
                    }`}
                  >
                    <div className="flex items-start justify-between gap-sm">
                      <span className="min-w-0">
                        <span className="block text-label-sm font-bold uppercase tracking-wider opacity-80">
                          {subject?.code ?? "Subject"}
                        </span>
                        <span className="mt-1 block font-semibold">{g.concept}</span>
                      </span>
                      <span className={`shrink-0 rounded-full px-xs py-1 text-label-sm ${STATUS_STYLES[g.status]}`}>
                        {g.status}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-8">
            {selected && (
              <>
                <div className={`mb-md rounded-xl border-l-4 px-md py-sm ${subjectTone(subject)}`}>
                  <p className="text-label-sm font-bold uppercase tracking-wider">Lesson · {subject?.code ?? "Current subject"}</p>
                  <h2 className="mt-1 text-headline-md font-bold text-on-surface">
                    {selected.concept}
                  </h2>
                </div>
                {loading && <p className="text-body-md text-on-surface-variant">Writing your lesson…</p>}
                {lesson && (
                  <div className="lesson-answer">
                    <TutorCard response={lesson} />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </States>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Practice -- the golden path ends here: answer wrong, see the diagnosis,
 * confirm or deny it. Confirmed is what feeds the teacher heatmap.
 * ------------------------------------------------------------------------- */
function PracticeView({ initialGap }: { initialGap: Gap | null }) {
  const [gaps, setGaps] = useState<Gap[] | null>(null);
  const [gap, setGap] = useState<Gap | null>(null);
  const [set, setSet] = useState<PracticeSet | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [results, setResults] = useState<Record<number, AnswerResult>>({});
  const [confirmState, setConfirmState] = useState<Record<number, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cached("gaps", getGaps)
      .then((r) => setGaps(r.items.filter((g) => g.status !== "closed")))
      .catch((err) => setError(errorText(err)));
  }, []);

  // "Practise" on the home card can hand us a specific gap.
  useEffect(() => {
    if (initialGap) setGap(initialGap);
  }, [initialGap]);

  async function loadFor(g: Gap) {
    setGap(g);
    setSet(null);
    setResults({});
    setConfirmState({});
    setError(null);
    try {
      // Resume a half-finished set rather than generating a new one;
      // null latest_practice_set_id means "offer the button", per contract.
      const s = g.latest_practice_set_id
        ? await cached(`practice:${g.latest_practice_set_id}`, () =>
            getPracticeSet(g.latest_practice_set_id!),
          )
        : await generatePractice(g.id);
      setSet(s);
      if (!g.latest_practice_set_id)
        invalidateCache("gaps"); // the gap now points at this set; a stale list would regenerate another
      const prior: Record<number, string> = {};
      const priorConfirm: Record<number, boolean> = {};
      for (const it of s.items) {
        if (it.your_answer) prior[it.id] = it.your_answer;
        if (it.diagnosis?.confirmed != null) priorConfirm[it.id] = it.diagnosis.confirmed;
      }
      setAnswers(prior);
      setConfirmState(priorConfirm);
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function answer(item: PracticeItemDto) {
    if (!set || !answers[item.id]) return;
    setBusy(true);
    setError(null);
    try {
      const r = await answerPractice(set.practice_set_id, item.id, answers[item.id]);
      // perf-002: the set now carries this answer; gaps/mastery may move too.
      invalidateCache(`practice:${set.practice_set_id}`, "gaps", "mastery");
      setResults((prev) => ({ ...prev, [item.id]: r }));
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function confirm(item: PracticeItemDto, yes: boolean) {
    const d = results[item.id]?.diagnosis ?? item.diagnosis;
    if (!d) return;
    setBusy(true);
    try {
      await confirmMisconception(d.id, yes);
      invalidateCache("gaps", "mastery"); // confirmed diagnoses feed teacher + gap status
      setConfirmState((prev) => ({ ...prev, [item.id]: yes }));
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="p-lg">
      <h1 className="mb-md text-headline-lg font-bold text-on-background">Practice</h1>

      <States
        loading={gaps === null}
        error={error}
        empty={!gaps?.length}
        emptyText="Take the diagnostic first — practice is generated from your gaps."
      >
        <div className="mb-md flex flex-wrap gap-xs">
          {(gaps ?? []).map((g) => (
            <button
              key={g.id}
              type="button"
              onClick={() => loadFor(g)}
              className={`rounded-full px-md py-xs text-label-md font-bold transition-colors ${
                gap?.id === g.id
                  ? "bg-forest-green text-white"
                  : "bg-sage-light text-on-surface hover:bg-mustard/20"
              }`}
            >
              {g.concept}
            </button>
          ))}
        </div>

        {error && <p role="alert" className="mb-md text-body-md text-error">{error}</p>}

        {!gap && <p className="text-body-md text-on-surface-variant">Pick a concept to practise.</p>}

        {set && (
          <div className="space-y-md">
            <p className="text-label-sm text-on-surface-variant">
              {set.concept} · {set.source === "generated" ? "generated for you" : set.source} ·
              {" "}{set.items.filter((i) => results[i.id]?.correct === true).length}/{set.items.length} correct so far
            </p>

            {set.items.map((item, i) => {
              const r = results[item.id];
              const diagnosis = r?.diagnosis ?? item.diagnosis;
              const confirmed = confirmState[item.id];
              return (
                <div
                  key={item.id}
                  className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm"
                >
                  <p className="mb-sm text-body-md font-semibold text-on-surface">
                    {i + 1}. {item.prompt}
                  </p>

                  {item.options && (
                    <div className="flex flex-col gap-xs">
                      {item.options.map((opt) => {
                        const chosen = answers[item.id] === opt;
                        const isRight = r && opt === r.correct_answer;
                        const isWrongChoice = r && chosen && !r.correct;
                        return (
                          <button
                            key={opt}
                            type="button"
                            disabled={!!r || busy}
                            onClick={() => setAnswers((a) => ({ ...a, [item.id]: opt }))}
                            className={`rounded-lg border p-sm text-left text-body-sm transition-colors ${
                              isRight
                                ? "border-forest-green bg-sage-light text-on-surface"
                                : isWrongChoice
                                  ? "border-error bg-error/10 text-on-surface"
                                  : chosen
                                    ? "border-forest-green bg-card text-on-surface"
                                    : "border-outline-variant/30 bg-card text-on-surface hover:border-forest-green/50"
                            }`}
                          >
                            {opt}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {!r && (
                    <button
                      type="button"
                      disabled={!answers[item.id] || busy}
                      onClick={() => answer(item)}
                      className="mt-sm rounded-lg bg-forest-green px-md py-xs text-label-md font-bold text-white hover:bg-forest-light disabled:opacity-50"
                    >
                      {busy ? "Checking…" : "Check answer"}
                    </button>
                  )}

                  {r && (
                    <div className={`mt-sm rounded-lg p-sm ${r.correct ? "bg-sage-light" : "bg-mustard/10"}`}>
                      <p className="flex items-center gap-xs text-body-sm font-bold text-on-surface">
                        {r.correct ? (
                          <>
                            <CheckCircle className="h-4 w-4 text-forest-green" /> Correct
                          </>
                        ) : (
                          <>
                            <XCircle className="h-4 w-4 text-error" /> Not quite — the answer is “{r.correct_answer}”
                          </>
                        )}
                      </p>
                      {r.explanation && (
                        <div className="mt-xs">
                          <Md>{r.explanation}</Md>
                        </div>
                      )}
                    </div>
                  )}

                  {/* The golden-path moment: a specific named misconception,
                      confirmed or denied BY THE STUDENT. Only confirmed feeds
                      the teacher heatmap. */}
                  {diagnosis && !diagnosis.confirmed && confirmed == null && (
                    <div className="mt-sm rounded-lg border border-mustard/50 bg-mustard/10 p-sm">
                      <p className="text-label-sm font-bold tracking-wider text-forest-green uppercase">
                        {diagnosis.label}
                      </p>
                      <p className="mt-xs text-body-sm text-on-surface">{diagnosis.question}</p>
                      <div className="mt-sm flex gap-sm">
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => confirm(item, true)}
                          className="rounded-lg bg-forest-green px-md py-xs text-label-md font-bold text-white hover:bg-forest-light disabled:opacity-50"
                        >
                          Yes, that's my thinking
                        </button>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => confirm(item, false)}
                          className="rounded-lg border border-outline-variant px-md py-xs text-label-md font-bold text-on-surface hover:bg-surface-container disabled:opacity-50"
                        >
                          No, not really
                        </button>
                      </div>
                    </div>
                  )}

                  {diagnosis && confirmed != null && (
                    <p className="mt-sm text-label-sm text-on-surface-variant">
                      {confirmed
                        ? "Confirmed — your teacher will see this in the class heatmap."
                        : "Denied — noted, and excluded from the class heatmap."}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </States>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Ask Tutor -- free questions, all three outcomes rendered by TutorCard.
 * ------------------------------------------------------------------------- */
function TutorView({ initialQuestion = "" }: { initialQuestion?: string }) {
  // tutor-002: the transcript lives on the server now. The chat seeds from
  // GET /tutor/history on mount and new turns append; a reload no longer
  // wipes the conversation. Each turn renders as a full TutorCard -- badge,
  // citations, and refusals included, since a refusal is an answer here.
  type ChatTurn =
    | { role: "user"; text: string }
    | { role: "tutor"; response: TutorResponse }
    | { role: "error"; text: string };
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (initialQuestion) setQuestion(initialQuestion);
  }, [initialQuestion]);

  useEffect(() => {
    let alive = true;
    cached("tutor-history", getTutorHistory)
      .then((items) => {
        if (!alive) return;
        setMessages(
          items.map((m) =>
            m.role === "student"
              ? { role: "user" as const, text: m.text ?? "" }
              : { role: "tutor" as const, response: m.response },
          ),
        );
      })
      .catch(() => {
        /* A history that won't load must not block asking; the chat just
           starts empty, as it always did before tutor-002. */
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || busy) return;
    setQuestion("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const response = await askTutor(q);
      invalidateCache("tutor-history"); // the pair just persisted server-side
      setMessages((m) => [...m, { role: "tutor", response }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "error", text: errorText(err) }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <div className="flex items-center justify-between px-lg py-md">
        <h1 className="text-headline-lg font-bold text-on-background">Ask Tutor</h1>
        <p className="text-label-sm text-on-surface-variant">
          Answers cite your course books · off-topic questions are refused, not guessed
        </p>
      </div>

      {/* Transcript */}
      <div className="flex-1 overflow-y-auto px-lg pb-sm">
        {messages.length === 0 && (
          <div className="mx-auto mt-xl max-w-[32rem] rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-lg text-center shadow-sm">
            <MessageCircle className="mx-auto mb-sm h-8 w-8 text-mustard" />
            <p className="text-body-md font-semibold text-on-surface">Ask anything about your course</p>
            <p className="mt-xs text-body-sm text-on-surface-variant">
              Every answer carries an evidence check against the approved corpus —
              the syllabus-alignment badge and page citations come from your own
              textbooks.
            </p>
          </div>
        )}

        <div className="mx-auto flex max-w-[44rem] flex-col gap-md">
          {messages.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="flex justify-end">
                <p className="max-w-[36rem] rounded-xl rounded-br-sm bg-forest-green px-md py-sm text-body-md text-white">
                  {m.text}
                </p>
              </div>
            ) : m.role === "error" ? (
              <p key={i} role="alert" className="rounded-xl border border-error/30 bg-error/10 p-md text-body-md text-error">
                {m.text}
              </p>
            ) : (
              <div key={i}>
                {/* tutor-003. The student typed "explain that more simply";
                    this is the standalone question that was actually retrieved
                    and scored. Shown so a wrong resolution is visible instead
                    of the tutor silently answering something else. Absent on
                    a question that needed no rewriting, which is most of them. */}
                {m.response.resolved_question && (
                  <p className="mb-xs text-label-sm text-on-surface-variant">
                    Answering: {m.response.resolved_question}
                  </p>
                )}
                <TutorCard response={m.response} />
              </div>
            ),
          )}
          {busy && (
            <p className="text-body-md text-on-surface-variant">Thinking…</p>
          )}
          <div ref={endRef} />
        </div>
      </div>

      {/* Composer */}
      <form
        onSubmit={ask}
        className="sticky bottom-0 border-t border-outline-variant bg-surface/90 px-lg py-sm backdrop-blur"
      >
        <div className="mx-auto flex max-w-[44rem] gap-sm">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a follow-up…"
            className="flex-1 rounded-full border border-outline-variant bg-card px-md py-sm text-body-md text-on-surface outline-none focus:border-forest-green"
          />
          <button
            type="submit"
            disabled={busy || !question.trim()}
            className="rounded-full bg-forest-green px-lg py-sm text-body-md font-bold text-white hover:bg-forest-light disabled:opacity-50"
          >
            {busy ? "…" : "Ask"}
          </button>
        </div>
      </form>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Assignments -- teacher-approved reteach units only.
 * ------------------------------------------------------------------------- */
function AssignmentsView() {
  const [items, setItems] = useState<Assignment[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cached("assignments", getAssignments)
      .then((r) => setItems(r.items))
      .catch((err) => setError(errorText(err)));
  }, []);

  return (
    <div className="p-lg">
      <h1 className="mb-md text-headline-lg font-bold text-on-background">Assignments</h1>
      <States
        loading={items === null}
        error={error}
        empty={!items?.length}
        emptyText="No reteach units assigned yet. When your teacher assigns one, it appears here."
      >
        <ul className="space-y-sm">
          {(items ?? []).map((a) => (
            <li
              key={a.id}
              className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm"
            >
              <div className="flex items-baseline justify-between gap-sm">
                <h2 className="text-body-md font-semibold text-on-surface">{a.title}</h2>
                <span className="text-label-sm text-on-surface-variant">
                  {a.assigned_at ? new Date(a.assigned_at).toLocaleDateString() : ""}
                </span>
              </div>
              <div className="mt-xs text-on-surface-variant">
                <Md>{a.body}</Md>
              </div>
            </li>
          ))}
        </ul>
      </States>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Settings -- language preference and logout, same semantics as the admin's.
 * ------------------------------------------------------------------------- */
function StudentSettingsView({ user, onUserChanged }: { user: User | null; onUserChanged: (u: User) => void }) {
  const navigate = useNavigate();
  const [langs, setLangs] = useState<{ code: string; label: string }[]>([]);
  const [langError, setLangError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getLanguages()
      .then((r) => setLangs(r.items))
      .catch((err) => setLangError(errorText(err)));
  }, []);

  async function changeLanguage(code: string) {
    setLangError(null);
    setBusy(true);
    try {
      onUserChanged(await updatePreferences(code));
      invalidateCache("me");
    } catch (err) {
      setLangError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function doLogout() {
    try {
      await logout();
    } catch {
      // token is unusable for anything real; drop it regardless
    } finally {
      clearToken(); // also drops the session cache (perf-002): the next student must not inherit this one's data
      navigate("/login", { replace: true });
    }
  }

  return (
    <div className="p-lg">
      <h1 className="mb-md text-headline-lg font-bold text-on-background">Settings</h1>

      <section className="mb-md rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
        <p className="mb-sm text-headline-sm font-semibold text-on-surface">Language</p>
        <p className="mb-sm text-body-sm text-on-surface-variant">
          Questions are answered in the language you pick — ask in Hindi, get Hindi back.
        </p>
        <select
          value={user?.preferred_language ?? "en"}
          disabled={busy || !user}
          onChange={(e) => changeLanguage(e.target.value)}
          className="rounded-lg border border-outline-variant bg-card px-md py-sm text-body-md text-on-surface outline-none focus:border-forest-green"
        >
          {langs.map((l) => (
            <option key={l.code} value={l.code}>
              {l.label}
            </option>
          ))}
        </select>
        {langError && (
          <p role="alert" className="mt-sm text-body-sm text-error">
            {langError}
          </p>
        )}
      </section>

      <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
        <p className="mb-sm text-headline-sm font-semibold text-on-surface">Session</p>
        <p className="mb-sm text-body-sm text-on-surface-variant">
          Logging out invalidates the session on the server, not just here.
        </p>
        <button
          type="button"
          onClick={doLogout}
          className="rounded-lg border border-error/40 px-md py-xs text-label-md font-bold text-error hover:bg-error/10"
        >
          Log out
        </button>
      </section>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Profile -- reached from the top-right avatar, like the admin console.
 * ------------------------------------------------------------------------- */
function ProfileView({ user, goto }: { user: User | null; goto: (s: Section) => void }) {
  const navigate = useNavigate();

  async function doLogout() {
    try {
      await logout();
    } catch {
      // the token is unusable for anything real; drop it regardless
    } finally {
      clearToken(); // also drops the session cache (perf-002): the next student must not inherit this one's data
      navigate("/login", { replace: true });
    }
  }

  return (
    <div className="p-lg">
      <h1 className="mb-md text-headline-lg font-bold text-on-background">Profile</h1>

      <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
        <div className="mb-md flex items-center gap-md">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-forest-green text-headline-md font-bold text-white">
            {user ? user.full_name.slice(0, 1).toUpperCase() : "…"}
          </div>
          <div>
            <h2 className="text-headline-md font-bold text-on-surface">
              {user ? user.full_name : "…"}
            </h2>
            <p className="text-label-md text-forest-green capitalize">
              {user ? user.role : ""}
            </p>
          </div>
        </div>

        <dl className="divide-y divide-outline-variant/10">
          <div className="flex items-baseline justify-between py-sm">
            <dt className="text-label-md text-on-surface-variant">Email</dt>
            <dd className="text-body-md text-on-surface">{user?.email ?? "…"}</dd>
          </div>
          <div className="flex items-baseline justify-between py-sm">
            <dt className="text-label-md text-on-surface-variant">Preferred language</dt>
            <dd className="text-body-md text-on-surface">
              {(user?.preferred_language ?? "en").toUpperCase()}
              <button
                type="button"
                onClick={() => goto("Settings")}
                className="ml-sm text-label-sm font-bold text-forest-green hover:underline"
              >
                change
              </button>
            </dd>
          </div>
        </dl>

        <div className="mt-md flex justify-end">
          <button
            type="button"
            onClick={doLogout}
            className="rounded-lg border border-error/40 px-md py-xs text-label-md font-bold text-error hover:bg-error/10"
          >
            Log out
          </button>
        </div>
      </section>
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * Shell
 * ------------------------------------------------------------------------- */
export default function Dashboard() {
  const [activeSection, setActiveSection] = useState<Section>("Dashboard");
  const [user, setUser] = useState<User | null>(null);

  // Shared so every "open this gap's lesson" click -- home card, gaps list,
  // Up Next -- lands in the Lessons section with that gap already selected.
  const [lessonGap, setLessonGap] = useState<Gap | null>(null);
  const [tutorQuestion, setTutorQuestion] = useState("");
  const openLesson = (g: Gap) => {
    setLessonGap(g);
    setActiveSection("Lessons");
  };
  const openTutor = (prompt: string) => {
    setTutorQuestion(prompt);
    setActiveSection("Ask Tutor");
  };

  useEffect(() => {
    cached("me", getMe)
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  return (
    <div className="min-h-screen bg-background text-on-background">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-50 flex h-full w-[240px] flex-col bg-forest-green">
        <div className="mb-md mt-sm p-lg">
          <span className="font-mono text-3xl font-bold tracking-widest text-white uppercase">
            JOURNEY
          </span>
        </div>

        <nav className="flex flex-1 flex-col overflow-y-auto px-sm">
          <div className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.label}
                  aria-current={activeSection === item.label ? "page" : undefined}
                  className={`font-mono flex w-full items-center rounded-lg px-sm py-3 text-left text-xs font-bold tracking-wider uppercase transition-all ${
                    activeSection === item.label
                      ? "border-l-4 border-[#e5b045] bg-forest-light text-white"
                      : "text-on-primary/70 hover:bg-forest-light hover:text-white"
                  }`}
                  onClick={() => setActiveSection(item.label)}
                  type="button"
                >
                  <Icon className="mr-sm h-5 w-5 shrink-0" />
                  {item.label}
                </button>
              );
            })}
          </div>

          <div className="flex-1" />

          <div className="mt-auto border-t border-on-primary/10 pt-4">
            <button
              aria-current={activeSection === "Settings" ? "page" : undefined}
              className={`font-mono mb-2 flex w-full items-center rounded-lg px-sm py-3 text-xs font-bold tracking-wider uppercase transition-all ${
                activeSection === "Settings"
                  ? "border-l-4 border-[#e5b045] bg-forest-light text-white"
                  : "text-on-primary/70 hover:bg-forest-light hover:text-white"
              }`}
              onClick={() => setActiveSection("Settings")}
              type="button"
            >
              <SettingsIcon className="mr-sm h-5 w-5 shrink-0" />
              Settings
            </button>
          </div>
        </nav>
      </aside>

      {/* Main application area */}
      <div className="w-full pl-[240px]">
        {/* Top header */}
        <header className="fixed left-[240px] right-0 top-0 z-40 flex h-16 items-center justify-end border-b border-outline-variant bg-surface/80 px-lg backdrop-blur-xl">
          <button
            type="button"
            onClick={() => setActiveSection("Profile")}
            aria-label="Open profile"
            className="group flex items-center gap-md"
          >
            <span className="text-body-sm font-semibold text-on-surface group-hover:underline">
              {user ? user.full_name : "…"}
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-forest-green text-label-md font-bold text-white transition-colors group-hover:bg-forest-light">
              {user ? user.full_name.slice(0, 1).toUpperCase() : "…"}
            </div>
          </button>
        </header>

        <main className="pt-16">
          {activeSection === "Dashboard" && (
            <HomeView user={user} goto={setActiveSection} openLesson={openLesson} />
          )}
          {activeSection === "My Course" && <MyCourseView />}
          {activeSection === "Diagnostic" && <DiagnosticView goto={setActiveSection} />}
          {activeSection === "My Gaps" && <GapsView openLesson={openLesson} askTutor={openTutor} />}
          {activeSection === "Lessons" && (
            <LessonsView selected={lessonGap} onSelect={setLessonGap} />
          )}
          {activeSection === "Practice" && <PracticeView initialGap={lessonGap} />}
          {activeSection === "Ask Tutor" && <TutorView initialQuestion={tutorQuestion} />}
          {activeSection === "Assignments" && <AssignmentsView />}
          {activeSection === "Profile" && <ProfileView user={user} goto={setActiveSection} />}
          {activeSection === "Settings" && (
            <StudentSettingsView user={user} onUserChanged={setUser} />
          )}
        </main>
      </div>
    </div>
  );
}
