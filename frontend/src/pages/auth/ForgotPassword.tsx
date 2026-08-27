import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

/**
 * auth-002, and the whole feature is this page. By contract there is NO
 * endpoint and deliberately no network call: collect an email, show
 * confirmation copy, stop. Do not add a fetch here -- the absence of
 * POST /auth/forgot-password is a decision recorded in docs/api-contract.md,
 * not an oversight.
 */
export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSent(true);
  }

  return (
    <div className="admin-scope min-h-screen bg-paper text-ink flex items-center justify-center p-4">
      <div className="bg-card rounded-3xl w-full max-w-[28rem] p-8 md:p-12 shadow-2xl">
        <Link
          to="/login"
          className="inline-flex items-center text-ink-soft hover:text-ink transition-colors mb-8"
        >
          <span className="material-symbols-outlined text-[18px] mr-1">
            arrow_back
          </span>
          Back
        </Link>

        <span className="text-ink-soft uppercase tracking-wider text-xs font-semibold">
          Account recovery
        </span>
        <h1 className="text-[32px] font-bold text-ink mt-2 mb-4 leading-tight">
          Forgot your password?
        </h1>

        {sent ? (
          <div>
            <p className="text-ink-soft mb-3">
              If an account exists for{" "}
              <span className="font-medium">{email}</span>, a password reset
              link has been sent to it.
            </p>
            <p className="text-ink-soft text-sm">
              Check your inbox and spam folder. The link expires in 24 hours.
            </p>
            <Link
              to="/login"
              className="inline-block w-full text-center bg-ink hover:bg-ink/90 text-white font-semibold py-3 rounded-lg transition-colors mt-8"
            >
              Back to login
            </Link>
          </div>
        ) : (
          <>
            <p className="text-ink-soft mb-8">
              Enter the email you registered with and we'll send you a reset
              link.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div>
                <label htmlFor="email" className="sr-only">Email</label>
                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email"
                  className="w-full px-4 py-3 rounded-lg border border-outline-variant bg-card focus:outline-none focus:ring-2 focus:ring-orange focus:border-transparent text-ink placeholder-ink-faint transition-shadow"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-ink hover:bg-ink/90 text-white font-semibold py-3 rounded-lg transition-colors mt-2 shadow-sm"
              >
                Send reset link
              </button>
            </form>

            <p className="text-center text-ink-soft text-sm mt-8">
              Remembered it?{" "}
              <Link to="/login" className="text-orange hover:underline font-medium">
                Log in
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
