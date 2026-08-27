import { useState } from "react";
import { useNavigate } from "react-router-dom";

/**
 * auth-004: signup is student-only. An admin account is seeded and a teacher
 * account is issued by their department admin (admin-009), so neither can
 * ever reach this screen -- it is part of the SIGNUP path, and only a
 * signed-in student gets here (guarded in App.tsx).
 */
type Role = "student";

export default function Onboarding1() {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState<Role>("student");

  const selectRole = (role: Role) => {
    setSelectedRole(role);
  };

  const handleContinue = () => {
    navigate("/onboarding/2");
  };

  // Skipping the welcome steps must still land in the app: this used to send
  // a freshly signed-up student back to the login screen they had just come
  // through.
  const handleSkip = () => {
    navigate("/onboarding/course");
  };

  return (
    <div className="dark">
      <div className="bg-background text-on-background min-h-screen flex flex-col font-body-md antialiased selection:bg-tertiary selection:text-on-tertiary">
        {/* Main Content Canvas */}
        <main className="flex-grow flex flex-col items-center justify-center px-container-padding py-section-gap w-full max-w-5xl mx-auto relative z-10 pb-12">
          
          {/* Progress Bar */}
          <div className="w-full max-w-[28rem] mx-auto mb-8 h-1 bg-surface-container-low rounded-full overflow-hidden">
            <div
              className="h-full bg-[#7AB139] transition-all duration-500"
              style={{ width: "50%" }}
            />
          </div>

          {/* Header */}
          <header className="text-center w-full mb-4">
            <p className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mb-4">
              Step 1 of 2
            </p>

            <h1 className="text-display-lg md:text-[56px] font-serif text-on-surface leading-tight tracking-tight">
              Who are you?
            </h1>
          </header>

          {/* Selection Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl justify-center">

            {/* Student */}
            <button
              type="button"
              onClick={() => selectRole("student")}
              className={`role-card glass-card rounded-[24px] p-card-inner-padding text-left flex flex-col items-start gap-4 border transition-all duration-300 group hover:-translate-y-1 focus:outline-none focus:ring-2 ${
                selectedRole === "student"
                  ? "border-brand-lavender/50 glow-active focus:ring-brand-lavender/50"
                  : "border-outline-variant focus:ring-brand-lavender/30"
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-brand-teal/20 flex items-center justify-center text-brand-lavender">
                <span
                  className="material-symbols-outlined text-3xl"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  school
                </span>
              </div>

              <div>
                <h3 className="text-headline-sm font-headline-sm text-on-surface mb-2">
                  Student
                </h3>

                <p className="text-body-md font-body-md text-on-surface-variant leading-relaxed">
                  I'm here to learn and track my progress through guided
                  materials.
                </p>
              </div>

              <div
                className={`mt-auto pt-4 w-full flex justify-end check-icon transition-opacity ${
                  selectedRole === "student"
                    ? "opacity-100"
                    : "opacity-0"
                }`}
              >
                <span className="material-symbols-outlined text-brand-lavender">
                  check_circle
                </span>
              </div>
            </button>

            {/* Teachers cannot sign up (auth-004): their department admin
                issues the account. Saying so here is friendlier than a card
                that would do nothing if clicked. */}
            <div className="glass-card rounded-[24px] p-card-inner-padding flex flex-col items-start gap-4 border border-outline-variant/40 opacity-80">
              <div className="w-12 h-12 rounded-full bg-brand-teal/5 flex items-center justify-center text-brand-teal">
                <span
                  className="material-symbols-outlined text-3xl"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  co_present
                </span>
              </div>

              <div>
                <h3 className="text-headline-sm font-headline-sm text-on-surface mb-2">
                  Teaching here?
                </h3>

                <p className="text-body-md font-body-md text-on-surface-variant leading-relaxed">
                  Your department admin creates your account and shares your
                  password — just log in, no signup needed.
                </p>
              </div>
            </div>


          </div>

          {/* Footer */}
          <footer className="w-full flex flex-col items-center justify-center pb-8 gap-4 px-container-padding mt-8 z-20">
            <button
              type="button"
              onClick={handleContinue}
              className="bg-surface-container border border-outline-variant/30 text-on-surface px-8 py-3 rounded-full text-label-md font-label-md tracking-wide btn-glow flex items-center gap-2"
            >
              Continue

              <span className="material-symbols-outlined text-sm">
                arrow_forward
              </span>
            </button>

            <button
              type="button"
              onClick={handleSkip}
              className="text-label-sm font-label-sm text-on-surface-variant hover:text-on-surface transition-colors underline underline-offset-4 decoration-on-surface-variant/50 hover:decoration-on-surface"
            >
              Skip for now
            </button>

            <p className="text-label-sm font-label-sm text-on-surface-variant/50 mt-2">
              ©️ 2026 Journey.
            </p>
          </footer>
        </main>

        {/* Decorative Background Elements */}
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-brand-teal/5 blur-[120px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-brand-lavender/5 blur-[150px]" />
        </div>
      </div>
    </div>
  );
}