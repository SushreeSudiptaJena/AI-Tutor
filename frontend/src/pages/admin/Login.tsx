import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";

type Role = "student" | "teacher" | "admin";

type User = {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  course_id?: number | null;
  preferred_language?: string;
};

type LoginResponse = {
  token: string;
  user: User;
};

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setLoading(true);

    try {
      const result = await api<LoginResponse>("/auth/login", {
        method: "POST",
        body: {
          email: email.trim(),
          password,
        },
        auth: false,
      });

      /*
       * Keep the token available for later authenticated requests.
       *
       * Your api.ts is the project's central API layer, so all future
       * requests should continue to go through api().
       */
      localStorage.setItem("token", result.token);
      localStorage.setItem(
        "user",
        JSON.stringify(result.user)
      );

      /*
       * The current App.tsx is not using React Router, so use normal
       * browser navigation for now.
       *
       * These routes can be converted to React Router routes later.
       */
      switch (result.user.role) {
        case "admin":
          window.location.href = "/admin";
          break;

        case "teacher":
          window.location.href = "/teacher";
          break;

        case "student":
          window.location.href = "/onboarding1";
          break;

        default:
          window.location.href = "/";
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(
          err.message || "Email or password is incorrect."
        );
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Email or password is incorrect.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f4f0e7",
        color: "#2b2926",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        fontFamily:
          '"Hanken Grotesk", Arial, sans-serif',
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1050px",
          minHeight: "620px",
          display: "flex",
          overflow: "hidden",
          borderRadius: "28px",
          background: "#ffffff",
          boxShadow:
            "0 25px 70px rgba(43, 41, 38, 0.16)",
        }}
      >
        {/* =====================================================
            LEFT PANEL
        ===================================================== */}

        <div
          style={{
            width: "46%",
            padding: "56px",
            display: "none",
            background:
              "linear-gradient(145deg, #e8dfd1, #f7f1e6)",
          }}
          className="login-left-panel"
        >
          <div
            style={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                fontFamily:
                  '"Courier Prime", monospace',
                fontSize: "11px",
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                color: "#c74620",
                marginBottom: "22px",
              }}
            >
              The Daily Edge
            </div>

            <h2
              style={{
                margin: 0,
                fontFamily:
                  '"EB Garamond", Georgia, serif',
                fontSize: "54px",
                lineHeight: "1.02",
                fontWeight: 600,
              }}
            >
              Knowledge is
              <br />
              the path,
              <br />
              not the peak.
            </h2>

            <div
              style={{
                width: "60px",
                height: "1px",
                background: "#e4552b",
                marginTop: "28px",
              }}
            />

            <p
              style={{
                marginTop: "24px",
                maxWidth: "360px",
                fontFamily:
                  '"Courier Prime", monospace',
                fontSize: "13px",
                lineHeight: "1.8",
                color: "#6f6862",
              }}
            >
              Learn from your course material,
              understand the reasoning, and build
              the confidence to solve the next
              problem yourself.
            </p>
          </div>
        </div>

        {/* =====================================================
            RIGHT PANEL
        ===================================================== */}

        <div
          style={{
            flex: 1,
            padding: "48px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <a
            href="/"
            style={{
              textDecoration: "none",
              color: "#6f6862",
              fontSize: "14px",
            }}
          >
            ← Back
          </a>

          <div
            style={{
              width: "100%",
              maxWidth: "430px",
              margin: "auto",
            }}
          >
            <div
              style={{
                fontFamily:
                  '"Courier Prime", monospace',
                fontSize: "10px",
                letterSpacing: "0.15em",
                textTransform: "uppercase",
                color: "#9c948b",
                marginBottom: "14px",
              }}
            >
              Welcome back
            </div>

            <h1
              style={{
                margin: "0 0 14px",
                fontFamily:
                  '"EB Garamond", Georgia, serif',
                fontSize: "48px",
                lineHeight: "1.05",
                fontWeight: 600,
                color: "#2b2926",
              }}
            >
              Continue your learning.
            </h1>

            <p
              style={{
                margin: "0 0 36px",
                color: "#6f6862",
                fontSize: "15px",
                lineHeight: "1.6",
              }}
            >
              Sign in to continue where you left off.
            </p>

            <form onSubmit={handleSubmit}>
              {/* EMAIL */}

              <label
                htmlFor="email"
                style={{
                  display: "block",
                  fontSize: "13px",
                  fontWeight: 600,
                  marginBottom: "8px",
                }}
              >
                Email
              </label>

              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                disabled={loading}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                style={{
                  width: "100%",
                  padding: "13px 14px",
                  borderRadius: "9px",
                  border: "1px solid #dedad4",
                  fontSize: "15px",
                  outline: "none",
                  marginBottom: "20px",
                }}
              />

              {/* PASSWORD */}

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px",
                }}
              >
                <label
                  htmlFor="password"
                  style={{
                    fontSize: "13px",
                    fontWeight: 600,
                  }}
                >
                  Password
                </label>

                <a
                  href="/forgot-password"
                  style={{
                    fontSize: "12px",
                    color: "#6f6862",
                    textDecoration: "none",
                  }}
                >
                  Forgot password?
                </a>
              </div>

              <div
                style={{
                  position: "relative",
                  marginBottom: "20px",
                }}
              >
                <input
                  id="password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={password}
                  disabled={loading}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  style={{
                    width: "100%",
                    padding: "13px 70px 13px 14px",
                    borderRadius: "9px",
                    border: "1px solid #dedad4",
                    fontSize: "15px",
                    outline: "none",
                  }}
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword(
                      (current) => !current
                    )
                  }
                  style={{
                    position: "absolute",
                    right: "12px",
                    top: "50%",
                    transform:
                      "translateY(-50%)",
                    border: 0,
                    background: "transparent",
                    color: "#6f6862",
                    cursor: "pointer",
                    fontSize: "12px",
                  }}
                >
                  {showPassword
                    ? "Hide"
                    : "Show"}
                </button>
              </div>

              {/* ERROR */}

              {error && (
                <div
                  role="alert"
                  style={{
                    marginBottom: "18px",
                    padding: "12px 14px",
                    borderRadius: "8px",
                    background: "#fff1ef",
                    border:
                      "1px solid #f0c6bf",
                    color: "#a63b2b",
                    fontSize: "13px",
                    lineHeight: "1.5",
                  }}
                >
                  {error}
                </div>
              )}

              {/* LOGIN BUTTON */}

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: "100%",
                  border: 0,
                  borderRadius: "9px",
                  padding: "14px",
                  background: loading
                    ? "#a8c980"
                    : "#7AB139",
                  color: "#ffffff",
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: loading
                    ? "not-allowed"
                    : "pointer",
                }}
              >
                {loading
                  ? "Logging in..."
                  : "Log in"}
              </button>
            </form>

            {/* SIGNUP */}

            <p
              style={{
                marginTop: "28px",
                textAlign: "center",
                fontSize: "13px",
                color: "#6f6862",
              }}
            >
              Don't have an account?{" "}
              <a
                href="/signup"
                style={{
                  color: "#7AB139",
                  fontWeight: 600,
                  textDecoration: "none",
                }}
              >
                Create account
              </a>
            </p>

            <div
              style={{
                marginTop: "36px",
                paddingTop: "18px",
                borderTop:
                  "1px solid #eeeeea",
                textAlign: "center",
                color: "#aaa39b",
                fontFamily:
                  '"Courier Prime", monospace',
                fontSize: "10px",
              }}
            >
              The Daily Edge — where knowledge comes alive.
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (min-width: 768px) {
          .login-left-panel {
            display: block !important;
          }
        }
      `}</style>
    </div>
  );
}