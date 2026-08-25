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
    <div className="admin-scope min-h-screen bg-gray-100 text-gray-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl w-full max-w-[28rem] p-8 md:p-12 shadow-2xl">
        <Link
          to="/login"
          className="inline-flex items-center text-gray-500 hover:text-gray-800 transition-colors mb-8"
        >
          <span className="material-symbols-outlined text-[18px] mr-1">
            arrow_back
          </span>
          Back
        </Link>

        <span className="text-gray-500 uppercase tracking-wider text-xs font-semibold">
          Account recovery
        </span>
        <h1 className="text-[32px] font-bold text-gray-900 mt-2 mb-4 leading-tight">
          Forgot your password?
        </h1>

        {sent ? (
          <div>
            <p className="text-gray-700 mb-3">
              If an account exists for{" "}
              <span className="font-medium">{email}</span>, a password reset
              link has been sent to it.
            </p>
            <p className="text-gray-500 text-sm">
              Check your inbox and spam folder. The link expires in 24 hours.
            </p>
            <Link
              to="/login"
              className="inline-block w-full text-center bg-[#7AB139] hover:bg-[#689a2f] text-white font-semibold py-3 rounded-lg transition-colors mt-8"
            >
              Back to login
            </Link>
          </div>
        ) : (
          <>
            <p className="text-gray-500 mb-8">
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
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7AB139] focus:border-transparent text-gray-900 placeholder-gray-400 transition-shadow"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-[#7AB139] hover:bg-[#689a2f] text-white font-semibold py-3 rounded-lg transition-colors mt-2 shadow-sm"
              >
                Send reset link
              </button>
            </form>

            <p className="text-center text-gray-500 text-sm mt-8">
              Remembered it?{" "}
              <Link to="/login" className="text-[#7AB139] hover:underline font-medium">
                Log in
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
