import { FormEvent, useState } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { api, ApiError, setToken, User } from "@/lib/api";

type LoginResponse = { token: string; user: User };

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [forgotMode, setForgotMode] = useState(false);
  const [forgotSubmitted, setForgotSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await api<LoginResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
        auth: false,
      });
      setToken(result.token);
      navigate(result.user.course_id ? "/dashboard" : "/onboarding/course");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to sign in right now.");
    } finally {
      setLoading(false);
    }
  }

  function submitForgot(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setForgotSubmitted(true);
  }

  return (
    <main className="flex min-h-screen bg-cream text-on-surface">
      <section className="hidden w-1/2 flex-col justify-between bg-forest-green p-xl text-white lg:flex">
        <div className="text-label-md font-bold tracking-[0.3em]">JOURNEY</div>
        <div className="max-w-[28rem]">
          <Sparkles className="mb-lg h-8 w-8 text-mustard" />
          <h1 className="font-serif text-6xl leading-tight">Learn with more clarity.</h1>
          <p className="mt-md text-body-lg text-white/70">
            A calmer way to understand what you know, find the gaps, and keep moving.
          </p>
        </div>
        <p className="text-label-sm text-white/50">PERSONALISED LEARNING / PHYSICS 101</p>
      </section>

      <section className="flex w-full items-center justify-center p-md sm:p-xl lg:w-1/2">
        <div className="w-full max-w-[28rem]">
          <div className="mb-xl lg:hidden">
            <span className="text-label-md font-bold tracking-[0.3em] text-forest-green">JOURNEY</span>
          </div>
          {forgotMode ? (
            <>
              <LockKeyhole className="mb-md h-7 w-7 text-forest-green" />
              <h2 className="font-serif text-4xl">Reset your password</h2>
              <p className="mt-sm text-body-md text-on-surface-variant">Enter your email and we&apos;ll confirm your request.</p>
              {forgotSubmitted ? (
                <div className="mt-lg border border-secondary/30 bg-sage-light p-md text-body-md text-forest-green">
                  If an account exists for that email, you&apos;ll receive next steps shortly.
                </div>
              ) : (
                <form className="mt-xl space-y-md" onSubmit={submitForgot}>
                  <label className="block text-label-md font-bold uppercase">Email address<input className="mt-xs w-full border border-outline-variant bg-white p-md outline-none focus:border-forest-green" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
                  <button className="flex w-full items-center justify-center gap-sm bg-forest-green p-md font-bold text-white hover:bg-forest-light" type="submit">Send request <ArrowRight className="h-4 w-4" /></button>
                </form>
              )}
              <button className="mt-lg text-label-md font-bold text-forest-green underline" onClick={() => { setForgotMode(false); setForgotSubmitted(false); }} type="button">Back to sign in</button>
            </>
          ) : (
            <>
              <h2 className="font-serif text-4xl">Welcome back.</h2>
              <p className="mt-sm text-body-md text-on-surface-variant">Pick up where your learning left off.</p>
              <form className="mt-xl space-y-md" onSubmit={submit}>
                <label className="block text-label-md font-bold uppercase">Email address<input className="mt-xs w-full border border-outline-variant bg-white p-md outline-none focus:border-forest-green" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
                <label className="block text-label-md font-bold uppercase">Password<div className="mt-xs flex border border-outline-variant bg-white"><input className="w-full border-0 bg-transparent p-md outline-none" type={showPassword ? "text" : "password"} required value={password} onChange={(event) => setPassword(event.target.value)} /><button className="px-md text-on-surface-variant" type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}</button></div></label>
                {error && <p className="border border-error/30 bg-error-container p-sm text-body-sm text-on-error-container" role="alert">{error}</p>}
                <button className="flex w-full items-center justify-center gap-sm bg-forest-green p-md font-bold text-white hover:bg-forest-light disabled:opacity-60" disabled={loading} type="submit">{loading ? "Signing in..." : "Sign in"} {!loading && <ArrowRight className="h-4 w-4" />}</button>
              </form>
              <button className="mt-md text-label-md font-bold text-forest-green underline" onClick={() => setForgotMode(true)} type="button">Forgot password?</button>
            </>
          )}
        </div>
      </section>
    </main>
  );
}