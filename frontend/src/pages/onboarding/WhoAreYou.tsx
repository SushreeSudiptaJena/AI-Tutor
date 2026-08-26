import { useState } from "react"
import { useNavigate } from "react-router-dom"

type Role = "student" | "teacher" | "other"

export default function WhoAreYou() {
  const navigate = useNavigate()
  const [selectedRole, setSelectedRole] = useState<Role>("student")

  function handleContinue() {
    localStorage.setItem("onboardingRole", selectedRole)
    navigate("/onboarding/what-do-you-use")
  }

  function handleSkip() {
    navigate("/onboarding/what-do-you-use")
  }

  return (
    <div className="min-h-screen bg-[#121414] text-[#e2e2e2] flex flex-col font-sans antialiased overflow-x-hidden">
      {/* Decorative Background */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[#0f766e]/5 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#fbcfe8]/5 blur-[150px]" />
      </div>

      {/* Main Content */}
      <main className="flex-grow flex flex-col items-center justify-center px-8 py-16 w-full max-w-5xl mx-auto relative z-10 pb-48">
        {/* Header */}
        <header className="text-center mb-12 w-full">
          <p className="text-[14px] leading-5 font-semibold text-[#c3c7ca] uppercase tracking-widest mb-4">
            Step 1 of 2
          </p>

          <h1 className="text-[48px] md:text-[56px] leading-tight font-serif font-bold text-[#e2e2e2] tracking-tight">
            Who are you?
          </h1>

          <p className="text-[18px] leading-7 text-[#c3c7ca] mt-4 max-w-[32rem] mx-auto">
            Select the role that best describes you to tailor your Journey
            experience.
          </p>
        </header>

        {/* Selection Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
          {/* Student */}
          <button
            type="button"
            onClick={() => setSelectedRole("student")}
            className={`
              bg-[rgba(30,32,32,0.6)]
              backdrop-blur-[16px]
              rounded-[24px]
              p-6
              text-left
              flex flex-col items-start gap-4
              border
              min-h-[260px]
              transition-all duration-300
              hover:-translate-y-1
              focus:outline-none
              focus:ring-2
              focus:ring-[#fbcfe8]/50
              ${
                selectedRole === "student"
                  ? "border-[#0f766e] shadow-[0_0_30px_rgba(251,207,232,0.2)]"
                  : "border-[#43474a] hover:border-[#0f766e]/50"
              }
            `}
          >
            <div className="w-12 h-12 rounded-full bg-[#0f766e]/20 flex items-center justify-center text-[#fbcfe8]">
              <span
                className="material-symbols-outlined text-3xl"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                school
              </span>
            </div>

            <div>
              <h3 className="text-[20px] leading-7 font-medium text-[#e2e2e2] mb-2">
                Student
              </h3>

              <p className="text-[16px] leading-6 text-[#c3c7ca]">
                I'm here to learn and track my progress through guided
                materials.
              </p>
            </div>

            <div className="mt-auto pt-4 w-full flex justify-end">
              {selectedRole === "student" ? (
                <span className="material-symbols-outlined text-[#fbcfe8]">
                  check_circle
                </span>
              ) : (
                <span className="material-symbols-outlined text-[#c3c7ca]">
                  arrow_forward
                </span>
              )}
            </div>
          </button>

          {/* Teacher */}
          <button
            type="button"
            onClick={() => setSelectedRole("teacher")}
            className={`
              bg-[rgba(30,32,32,0.6)]
              backdrop-blur-[16px]
              rounded-[24px]
              p-6
              text-left
              flex flex-col items-start gap-4
              border
              min-h-[260px]
              transition-all duration-300
              hover:-translate-y-1
              focus:outline-none
              focus:ring-2
              focus:ring-[#c2410c]/30
              ${
                selectedRole === "teacher"
                  ? "border-[#c2410c] shadow-[0_0_30px_rgba(194,65,12,0.2)]"
                  : "border-[#43474a] hover:border-[#c2410c]/50"
              }
            `}
          >
            <div className="w-12 h-12 rounded-full bg-[#c2410c]/10 flex items-center justify-center text-[#c2410c]">
              <span className="material-symbols-outlined text-3xl">
                supervisor_account
              </span>
            </div>

            <div>
              <h3 className="text-[20px] leading-7 font-medium text-[#e2e2e2] mb-2">
                Teacher
              </h3>

              <p className="text-[16px] leading-6 text-[#c3c7ca]">
                I want to guide, create curriculum, and monitor learners'
                academic journeys.
              </p>
            </div>

            <div className="mt-auto pt-4 w-full flex justify-end">
              {selectedRole === "teacher" ? (
                <span className="material-symbols-outlined text-[#fbcfe8]">
                  check_circle
                </span>
              ) : (
                <span className="material-symbols-outlined text-[#c3c7ca]">
                  arrow_forward
                </span>
              )}
            </div>
          </button>

          {/* Other / Self-learner */}
          <button
            type="button"
            onClick={() => setSelectedRole("other")}
            className={`
              bg-[rgba(30,32,32,0.6)]
              backdrop-blur-[16px]
              rounded-[24px]
              p-6
              text-left
              flex flex-col items-start gap-4
              border
              min-h-[260px]
              transition-all duration-300
              hover:-translate-y-1
              focus:outline-none
              focus:ring-2
              focus:ring-[#9f1239]/30
              ${
                selectedRole === "other"
                  ? "border-[#9f1239] shadow-[0_0_30px_rgba(159,18,57,0.2)]"
                  : "border-[#43474a] hover:border-[#9f1239]/50"
              }
            `}
          >
            <div className="w-12 h-12 rounded-full bg-[#9f1239]/10 flex items-center justify-center text-[#fbcfe8]">
              <span className="material-symbols-outlined text-3xl">
                local_library
              </span>
            </div>

            <div>
              <h3 className="text-[20px] leading-7 font-medium text-[#e2e2e2] mb-2">
                Other / Self-learner
              </h3>

              <p className="text-[16px] leading-6 text-[#c3c7ca]">
                I'm here for personal growth, independent research, and
                curiosity.
              </p>
            </div>

            <div className="mt-auto pt-4 w-full flex justify-end">
              {selectedRole === "other" ? (
                <span className="material-symbols-outlined text-[#fbcfe8]">
                  check_circle
                </span>
              ) : (
                <span className="material-symbols-outlined text-[#c3c7ca]">
                  arrow_forward
                </span>
              )}
            </div>
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 w-full flex flex-col items-center justify-center pb-8 gap-4 px-8 bg-gradient-to-t from-[#121414] via-[#121414]/95 to-transparent pt-12 z-20">
        <button
          type="button"
          onClick={handleContinue}
          className="bg-[#1e2020] border border-[#43474a]/30 text-[#e2e2e2] px-8 py-3 rounded-full text-[14px] font-semibold tracking-wide flex items-center gap-2 shadow-[0_4px_20px_rgba(251,207,232,0.3)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_6px_25px_rgba(251,207,232,0.5)]"
        >
          Continue

          <span className="material-symbols-outlined text-sm">
            arrow_forward
          </span>
        </button>

        <button
          type="button"
          onClick={handleSkip}
          className="text-[12px] font-medium text-[#c3c7ca] hover:text-[#e2e2e2] transition-colors underline underline-offset-4"
        >
          Skip for now
        </button>

        <p className="text-[12px] font-medium text-[#c3c7ca]/50 mt-2">
          © 2026 Journey.
        </p>
      </footer>
    </div>
  )
}