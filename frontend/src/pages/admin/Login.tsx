import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"
import { AuthLayout } from "@/components/AuthLayout"
import { login, setToken, ApiError } from "@/lib/api"
import { USE_MOCK, mockLogin } from "@/lib/mock"

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { token, user } = USE_MOCK ? await mockLogin(email, password) : await login(email, password)
      setToken(token)
      navigate(user.role === "admin" ? "/admin" : "/onboarding/role")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't log in. Try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <h1 className="text-headline-lg text-on-surface mb-2">Welcome back</h1>
      <p className="text-on-surface-variant text-sm mb-8">Log in to continue your work.</p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
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
            className="w-full rounded-md bg-surface-container border border-outline-variant px-4 py-3 text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-tertiary"
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
            className="w-full rounded-md bg-surface-container border border-outline-variant px-4 py-3 pr-12 text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-tertiary"
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface text-xs"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>

        <div className="flex justify-end">
          <Link to="/forgot-password" className="text-xs text-on-surface-variant hover:text-on-surface underline underline-offset-4">
            Forgot password?
          </Link>
        </div>

        {error && (
          <p role="alert" className="text-error text-sm">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-primary-glow text-on-tertiary text-label-md px-8 py-3 rounded-full w-full text-center"
        >
          {loading ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="text-center text-on-surface-variant text-sm mt-6">
        Don't have an account?{" "}
        <Link to="/signup" className="text-tertiary hover:underline underline-offset-4">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  )
}