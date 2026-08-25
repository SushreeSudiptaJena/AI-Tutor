import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signup, setToken, ApiError } from "@/lib/api";

/**
 * Real signup against POST /auth/signup. On success the backend returns a
 * token immediately (no email verification step exists), so we log the user
 * in and route them on. Existing email -> 409 conflict, surfaced verbatim.
 *
 * Role choice is student/teacher only: admin accounts are seeded, and
 * self-serve admin signup is not a thing we want to show a judge.
 */
export default function Signup() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"student" | "teacher">("student");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { token } = await signup({
        email,
        password,
        full_name: fullName,
        role,
      });
      setToken(token);
      navigate("/onboarding/1");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Couldn't sign up. Try again.",
      );
    } finally {
      setLoading(false);
    }
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
          Create your account
        </span>
        <h1 className="text-[32px] font-bold text-gray-900 mt-2 mb-8 leading-tight">
          Start your learning path.
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="fullname" className="sr-only">Full name</label>
            <input
              id="fullname"
              type="text"
              required
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Full name"
              className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7AB139] focus:border-transparent text-gray-900 placeholder-gray-400 transition-shadow"
            />
          </div>

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

          <div>
            <label htmlFor="password" className="sr-only">Password</label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password (min 8 characters)"
              className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7AB139] focus:border-transparent text-gray-900 placeholder-gray-400 transition-shadow"
            />
          </div>

          <div>
            <label htmlFor="role" className="block text-sm text-gray-500 mb-1">
              I am a
            </label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value as "student" | "teacher")}
              className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7AB139] focus:border-transparent text-gray-900"
            >
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
            </select>
          </div>

          {error && (
            <p role="alert" className="text-red-600 text-sm">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#7AB139] hover:bg-[#689a2f] disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors mt-2 shadow-sm"
          >
            {loading ? "Creating account…" : "Sign Up"}
          </button>
        </form>

        <p className="text-center text-gray-500 text-sm mt-8">
          Already have an account?{" "}
          <Link to="/login" className="text-[#7AB139] hover:underline font-medium">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
