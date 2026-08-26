import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login, setToken, ApiError } from "@/lib/api";
import screenImage from "@/assets/admin-login.jpeg";

/**
 * The unified door (auth-004): students AND teachers sign in here. Admins
 * have their own console door at /admin/login. Same design as the admin
 * login -- one visual language for every auth screen.
 *
 * Routing is role-first: a teacher has a course_id too, so routing on
 * course_id alone would bounce them off the student dashboard.
 */
export default function UnifiedLogin() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { token, user } = await login(email, password);
      setToken(token);
      if (user.role === "teacher") navigate("/teacher");
      else if (user.role === "admin") navigate("/admin");
      else navigate(user.course_id ? "/dashboard" : "/onboarding/course");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't log in. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="admin-scope min-h-screen bg-gray-100 text-gray-900 relative overflow-y-auto">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-[#243138] via-[#121414] to-[#1e3600]" />
        <div className="absolute inset-0 bg-black/20" />
      </div>

      <nav className="relative z-10 w-full absolute top-0 left-0">
        <div className="flex justify-between items-center px-8 py-6 w-full max-w-7xl mx-auto">
          <div className="text-white text-2xl font-bold">Journey</div>
          <div className="hidden md:flex items-center gap-6 ml-auto mr-8">
            <Link to="/" className="text-white/80 hover:text-white transition-colors">
              Home
            </Link>
          </div>
          <Link
            to="/signup"
            className="px-6 py-2 rounded-full border border-white/40 text-white hover:bg-white/10 transition-colors"
          >
            Sign Up
          </Link>
        </div>
      </nav>

      <main className="relative z-10 min-h-screen flex items-center justify-center p-4 w-full">
        <div className="bg-white rounded-3xl w-full max-w-5xl flex overflow-hidden shadow-2xl min-h-[600px] mt-8 mb-8">
          <div className="hidden md:block md:w-[46%] relative bg-gray-100">
            <div className="w-full h-full overflow-hidden">
              <img
                src={screenImage}
                alt="A winding forest path toward distant peaks"
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          <div className="w-full md:w-[54%] p-8 md:p-12 lg:p-16 flex flex-col relative bg-white">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center text-gray-500 hover:text-gray-800 transition-colors mb-8 w-fit"
            >
              <span className="material-symbols-outlined text-[18px] mr-1">arrow_back</span>
              Back
            </button>

            <div className="flex-grow flex flex-col justify-center max-w-[28rem] mx-auto w-full">
              <span className="text-gray-500 uppercase tracking-wider text-xs font-semibold mb-4">
                Students & teachers
              </span>
              <h1 className="font-serif text-[42px] font-bold text-gray-900 mb-10 leading-tight">
                Knowledge is the path, not the peak.
              </h1>

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

                <div className="relative">
                  <label htmlFor="password" className="sr-only">Password</label>
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Password"
                    className="w-full px-4 py-3 pr-12 rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#7AB139] focus:border-transparent text-gray-900 placeholder-gray-400 transition-shadow"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    <span className="material-symbols-outlined text-[20px]">
                      {showPassword ? "visibility_off" : "visibility"}
                    </span>
                  </button>
                </div>

                <div className="flex justify-end pt-1">
                  <Link
                    to="/forgot-password"
                    className="text-sm text-gray-500 hover:text-gray-800 transition-colors"
                  >
                    Forgot Password?
                  </Link>
                </div>

                {error && (
                  <p role="alert" className="text-red-600 text-sm">{error}</p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#7AB139] hover:bg-[#689a2f] disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors mt-6 shadow-sm"
                >
                  {loading ? "Logging in…" : "Log In"}
                </button>
              </form>

              <p className="text-center text-gray-500 text-sm mt-8 mb-2">
                Don't have an account?{" "}
                <Link to="/signup" className="text-[#7AB139] hover:underline font-medium">
                  Sign up
                </Link>
              </p>
              <p className="text-center text-gray-400 text-xs mb-6">
                Teachers can't self-sign-up — your department admin issues your password.
              </p>

              <div className="mt-auto pt-4 border-t border-gray-100 flex items-center justify-center text-gray-400 text-xs">
                <span className="material-symbols-outlined text-[16px] mr-2">school</span>
                <span>Journey — where knowledge comes alive</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
