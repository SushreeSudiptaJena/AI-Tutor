import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, ClipboardCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "@/lib/api";

type Item = { id: number; prompt: string; options?: string[] | null };
type Diagnostic = { diagnostic_id: number; items: Item[] };

export default function OnboardingDiagnostic() {
  const navigate = useNavigate();
  const [diagnostic, setDiagnostic] = useState<Diagnostic | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api<Diagnostic>("/student/diagnostic").then(setDiagnostic).catch((caught) => setError(caught instanceof ApiError ? caught.message : "Diagnostic is unavailable."));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!diagnostic) return;
    setSubmitting(true);
    setError("");
    try {
      await api(`/student/diagnostic/${diagnostic.diagnostic_id}/submit`, { method: "POST", body: { answers: Object.entries(answers).map(([item_id, answer]) => ({ item_id: Number(item_id), answer })) } });
      navigate("/dashboard");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "We could not save your answers.");
    } finally { setSubmitting(false); }
  }

  return (
    <main className="min-h-screen bg-cream px-md py-xl text-on-surface sm:px-xl">
      <div className="mx-auto max-w-3xl"><p className="text-label-md font-bold tracking-[0.3em] text-forest-green">JOURNEY / 02</p><div className="mt-xl flex items-start gap-md"><ClipboardCheck className="mt-xs h-9 w-9 shrink-0 text-mustard" /><div><h1 className="font-serif text-5xl leading-tight">A quick starting point.</h1><p className="mt-md text-body-lg text-on-surface-variant">Answer honestly. This finds prerequisite gaps, not grades.</p></div></div>
        <form className="mt-xl space-y-md" onSubmit={submit}>{diagnostic?.items.map((item, index) => <fieldset className="border border-outline-variant bg-card p-lg" key={item.id}><legend className="text-label-md font-bold text-forest-green">QUESTION {index + 1}</legend><p className="mt-sm text-body-lg font-bold">{item.prompt}</p><div className="mt-md space-y-sm">{item.options?.map((option) => <label className="flex cursor-pointer gap-sm border border-outline-variant p-sm hover:bg-sage-light" key={option}><input required type="radio" name={`item-${item.id}`} value={option} checked={answers[item.id] === option} onChange={() => setAnswers({ ...answers, [item.id]: option })} />{option}</label>) ?? <input className="mt-sm w-full border border-outline-variant p-md" required value={answers[item.id] ?? ""} onChange={(event) => setAnswers({ ...answers, [item.id]: event.target.value })} />}</div></fieldset>)}{error && <p className="border border-error/30 bg-error-container p-sm text-on-error-container" role="alert">{error}</p>}<button className="flex items-center gap-sm bg-forest-green px-lg py-md font-bold text-white hover:bg-forest-light disabled:opacity-60" disabled={!diagnostic || submitting} type="submit">{submitting ? "Saving..." : "See my learning path"} {!submitting && <ArrowRight className="h-4 w-4" />}</button></form>
      </div>
    </main>
  );
}