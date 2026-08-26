import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signup, setToken, ApiError } from "@/lib/api";

/**
 * Student signup (auth-004): teachers are issued passwords by their
 * department admin and never sign themselves up. Enrolment -- university +
 * roll number -- is captured here; verification is deliberately not built
 * ("all are welcome" for this build). Existing email -> 409, surfaced verbatim.
 */
const UNIVERSITIES = [
  "Siksha 'O' Anusandhan",
  "KIIT University",
  "VSSUT Burla",
  "IIT Bhubaneswar",
  "Other",
];

export default function Signup() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [university, setUniversity] = useState(UNIVERSITIES[0]);
  const [rollNumber, setRollNumber] = useState("");
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
        university,
        roll_number: rollNumber.trim() || undefined,
      });
      setToken(token);
      navigate("/onboarding/course");
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
        <div className="flex flex-col">
          <Link
            to="/admin/login"
            className="inline-flex w-fit items-center text-gray-500 hover:text-gray-800 transition-colors -ml-1 mb-6"
          >
            <span className="material-symbols-outlined text-[18px] mr-1">
              arrow_back
            </span>
            Back
          </Link>

          <span className="text-gray-500 uppercase tracking-wider text-xs font-semibold">
            Create your account
          </span>
        </div>
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
            <label htmlFor="university" className="block text-sm text-gray-500 mb-1">
              University
            </label>
            <select
              id="university"
              value={university}
              onChange={(e) => setUniversity(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7AB139] focus:border-transparent text-gray-900"
            >
              {UNIVERSITIES.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="rollno" className="sr-only">Registration / roll number</label>
            <input
              id="rollno"
              type="text"
              autoComplete="off"
              value={rollNumber}
              onChange={(e) => setRollNumber(e.target.value)}
              placeholder="Registration / roll number (optional)"
              className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7AB139] focus:border-transparent text-gray-900 placeholder-gray-400 transition-shadow"
            />
            <p className="text-xs text-gray-400 mt-1">
              Used to enrol you in your university's courses. Everyone is welcome in this build.
            </p>
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
          <Link to="/admin/login" className="text-[#7AB139] hover:underline font-medium">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
