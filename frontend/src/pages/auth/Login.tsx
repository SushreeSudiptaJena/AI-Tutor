import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login, setToken, ApiError } from "@/lib/api";
import { USE_MOCK, mockLogin } from "@/lib/mock";
import screenImage from "@/assets/login-illustration.png";

export default function Login() {
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
      const { token, user } = USE_MOCK
        ? await mockLogin(email, password)
        : await login(email, password);

      setToken(token);

      if (user.role === "admin") {
        navigate("/admin");
      } else {
        navigate("/onboarding/1");
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Couldn't log in. Try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="admin-scope min-h-screen bg-gray-100 text-gray-900 relative overflow-y-auto">

      {/* Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-[#243138] via-[#121414] to-[#1e3600]" />
        <div className="absolute inset-0 bg-black/20" />
      </div>

      {/* Top Navigation */}
      <nav className="relative z-10 w-full absolute top-0 left-0">
        <div className="flex justify-between items-center px-8 py-6 w-full max-w-7xl mx-auto">

          {/* Logo */}
          <div className="text-white text-2xl font-bold">
            Nocturnal Scholar
          </div>

          {/* Navigation */}
          <div className="hidden md:flex items-center gap-6 ml-auto mr-8">
            <Link
              to="/"
              className="text-white/80 hover:text-white transition-colors"
            >
              Home
            </Link>

            <a
              href="#"
              className="text-white/80 hover:text-white transition-colors"
            >
              About
            </a>
          </div>

          {/* Sign Up */}
          <Link
            to="/signup"
            className="px-6 py-2 rounded-full border border-white/40 text-white hover:bg-white/10 transition-colors"
          >
            Sign Up
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 min-h-screen flex items-center justify-center p-4 w-full">

        <div className="bg-white rounded-3xl w-full max-w-5xl flex overflow-hidden shadow-2xl min-h-[600px] mt-8 mb-8">

          {/* LEFT IMAGE PANEL */}
          <div className="hidden md:block md:w-[46%] relative bg-gray-100">

            <div className="w-full h-full overflow-hidden">

              <img
                src={screenImage}
                alt="Mountain path illustration"
                className="w-full h-full object-cover"
              />

            </div>
          </div>

          {/* RIGHT LOGIN PANEL */}
          <div className="w-full md:w-[54%] p-8 md:p-12 lg:p-16 flex flex-col relative bg-white">

            {/* Back Button */}
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center text-gray-500 hover:text-gray-800 transition-colors mb-8 w-fit"
            >
              <span className="material-symbols-outlined text-[18px] mr-1">
                arrow_back
              </span>

              Back
            </button>

            <div className="flex-grow flex flex-col justify-center max-w-md mx-auto w-full">

              {/* Small heading */}
              <span className="text-gray-500 uppercase tracking-wider text-xs font-semibold mb-4">
                Welcome back
              </span>

              {/* Main heading */}
              <h1 className="font-serif text-[42px] font-bold text-gray-900 mb-10 leading-tight">
                Knowledge is the path, not the peak.
              </h1>

              {/* LOGIN FORM */}
              <form
                onSubmit={handleSubmit}
                className="space-y-4"
                noValidate
              >

                {/* Email */}
                <div>
                  <label
                    htmlFor="email"
                    className="sr-only"
                  >
                    Email
                  </label>

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

                {/* Password */}
                <div className="relative">

                  <label
                    htmlFor="password"
                    className="sr-only"
                  >
                    Password
                  </label>

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

                  {/* Password visibility */}
                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword((value) => !value)
                    }
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                  >
                    <span className="material-symbols-outlined text-[20px]">
                      {showPassword
                        ? "visibility_off"
                        : "visibility"}
                    </span>
                  </button>

                </div>

                {/* Forgot Password */}
                <div className="flex justify-end pt-1">

                  <Link
                    to="/forgot-password"
                    className="text-sm text-gray-500 hover:text-gray-800 transition-colors"
                  >
                    Forgot Password?
                  </Link>

                </div>

                {/* Error */}
                {error && (
                  <p
                    role="alert"
                    className="text-red-600 text-sm"
                  >
                    {error}
                  </p>
                )}

                {/* Login Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#7AB139] hover:bg-[#689a2f] disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors mt-6 shadow-sm"
                >
                  {loading
                    ? "Logging in…"
                    : "Log In"}
                </button>

              </form>

              {/* Divider */}
              <div className="relative flex items-center py-6">

                <div className="flex-grow border-t border-gray-200" />

                <span className="flex-shrink-0 mx-4 text-gray-400 text-sm">
                  Or continue with
                </span>

                <div className="flex-grow border-t border-gray-200" />

              </div>

              {/* Google Button */}
              <button
                type="button"
                className="w-full flex items-center justify-center bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 font-semibold py-3 rounded-lg transition-colors shadow-sm"
              >

                <svg
                  className="w-5 h-5 mr-3"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />

                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />

                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />

                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>

                Continue with Google

              </button>

              {/* Sign Up */}
              <p className="text-center text-gray-500 text-sm mt-8 mb-6">

                Don't have an account?{" "}

                <Link
                  to="/signup"
                  className="text-[#7AB139] hover:underline font-medium"
                >
                  Sign up
                </Link>

              </p>

              {/* Footer */}
              <div className="mt-auto pt-4 border-t border-gray-100 flex items-center justify-center text-gray-400 text-xs">

                <span className="material-symbols-outlined text-[16px] mr-2">
                  school
                </span>

                <span>
                  Nocturnal Scholar — Where Knowledge Comes Alive
                </span>

              </div>

            </div>
          </div>

        </div>
      </main>
    </div>
  );
}