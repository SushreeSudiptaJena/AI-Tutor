import { useEffect, useState } from "react";
import { ArrowRight, BookOpen } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "@/lib/api";

type CourseSummary = { course: { code: string; title: string }; books: { title: string }[]; topics: { name: string }[] };

export default function OnboardingCourse() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<CourseSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<CourseSummary>("/student/course-summary").then(setSummary).catch((caught) => {
      setError(caught instanceof ApiError ? caught.message : "Course details are unavailable.");
    });
  }, []);

  return (
    <main className="min-h-screen bg-cream px-md py-xl text-on-surface sm:px-xl">
      <div className="mx-auto max-w-3xl">
        <p className="text-label-md font-bold tracking-[0.3em] text-forest-green">JOURNEY / 01</p>
        <div className="mt-xl grid gap-xl md:grid-cols-[0.8fr_1.2fr] md:items-center">
          <div><BookOpen className="h-10 w-10 text-mustard" /><h1 className="mt-md font-serif text-5xl leading-tight">Start with your course.</h1><p className="mt-md text-body-lg text-on-surface-variant">We&apos;ll use your syllabus to make every next step more useful.</p></div>
          <div className="border border-outline-variant bg-white p-lg shadow-sm">
            {error ? <p className="text-error" role="alert">{error}</p> : summary ? <><p className="text-label-md font-bold text-forest-green">{summary.course.code}</p><h2 className="mt-xs text-headline-md font-bold">{summary.course.title}</h2><p className="mt-md text-body-sm text-on-surface-variant">{summary.books.length} course resource{summary.books.length === 1 ? "" : "s"} · {summary.topics.length} topics ready</p><div className="mt-lg flex flex-wrap gap-xs">{summary.topics.slice(0, 5).map((topic) => <span className="bg-sage-light px-sm py-xs text-label-sm" key={topic.name}>{topic.name}</span>)}</div></> : <p className="text-on-surface-variant">Loading your course...</p>}
          </div>
        </div>
        <button className="mt-xl flex items-center gap-sm bg-forest-green px-lg py-md font-bold text-white hover:bg-forest-light" onClick={() => navigate("/onboarding/diagnostic")} type="button">Continue <ArrowRight className="h-4 w-4" /></button>
      </div>
    </main>
  );
}