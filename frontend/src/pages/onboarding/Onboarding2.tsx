import { useState } from "react";
import { useNavigate } from "react-router-dom";

type LearningOption =
  | "homework"
  | "exam"
  | "coding"
  | "creative"
  | "general"
  | "other";

const options: {
  id: LearningOption;
  icon: string;
  label: string;
}[] = [
  {
    id: "homework",
    icon: "book",
    label: "Homework help",
  },
  {
    id: "exam",
    icon: "school",
    label: "Exam preparation",
  },
  {
    id: "coding",
    icon: "code",
    label: "Coding / Technical learning",
  },
  {
    id: "creative",
    icon: "palette",
    label: "Creative / Design learning",
  },
  {
    id: "general",
    icon: "public",
    label: "General knowledge / Curiosity",
  },
  {
    id: "other",
    icon: "more_horiz",
    label: "Other",
  },
];

export default function Onboarding2() {
  const navigate = useNavigate();

  // These match the original HTML:
  // Coding and General knowledge start selected.
  const [selectedOptions, setSelectedOptions] = useState<LearningOption[]>([
    "coding",
    "general",
  ]);

  const toggleOption = (option: LearningOption) => {
    setSelectedOptions((current) =>
      current.includes(option)
        ? current.filter((item) => item !== option)
        : [...current, option]
    );
  };

  // Both paths go ON into the app. They used to return a freshly signed-up
  // student to the login screen, which read as "your signup failed".
  const handleContinue = () => {
    navigate("/onboarding/course");
  };

  const handleSkip = () => {
    navigate("/onboarding/course");
  };

  return (
    <div className="dark">
      <div className="bg-background text-on-background min-h-screen flex flex-col items-center justify-center font-body-md overflow-x-hidden selection:bg-tertiary selection:text-on-tertiary relative">

        {/* Progress bar */}
        <div className="fixed top-0 left-0 w-full h-1 bg-surface-container z-50">
          <div
            className="h-full w-full bg-tertiary"
            style={{ backgroundColor: "#7AB139" }}
          />
        </div>

        {/* Main Content */}
        <main className="w-full max-w-4xl px-container-padding py-section-gap flex flex-col items-center justify-center flex-grow z-10 relative">

          {/* Step Indicator */}
          <div className="mb-8">
            <span className="text-on-surface-variant font-label-md text-label-md tracking-widest uppercase">
              Step 2 of 2
            </span>
          </div>

          {/* Heading */}
          <div className="text-center max-w-2xl mb-8">
            <h1
              className="font-display-lg text-display-lg text-primary tracking-tight mb-2"
              style={{
                fontFamily: '"DM Serif Display", serif',
                fontWeight: 700,
              }}
            >
              What will you use this for?
            </h1>
          </div>

          {/* Selection Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-gutter w-full mb-section-gap">

            {options.map((option) => {
              const isSelected = selectedOptions.includes(option.id);

              return (
                <button
                  key={option.id}
                  type="button"
                  aria-pressed={isSelected}
                  onClick={() => toggleOption(option.id)}
                  className={`glass-card rounded-xl p-card-inner-padding flex flex-col items-center justify-center gap-4 text-center group cursor-pointer h-48 focus:outline-none focus:ring-2 focus:ring-tertiary ${
                    isSelected ? "selected" : ""
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-4xl transition-colors ${
                      isSelected
                        ? "text-tertiary"
                        : "text-on-surface-variant group-hover:text-primary"
                    }`}
                    style={{
                      fontVariationSettings: isSelected
                        ? "'FILL' 1"
                        : "'FILL' 0",
                    }}
                  >
                    {option.icon}
                  </span>

                  <span className="font-headline-sm text-headline-sm text-on-surface">
                    {option.label}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Footer */}
          <footer className="w-full flex flex-col items-center justify-center pb-8 gap-4 px-container-padding mt-8 z-20">

            <button
              type="button"
              onClick={handleContinue}
              className="bg-tertiary text-on-tertiary font-label-md text-label-md px-8 py-3 rounded-full w-64 text-center flex justify-center items-center gap-2 btn-primary-glow"
              style={{ backgroundColor: "#7AB139" }}
            >
              Continue

              <span className="material-symbols-outlined text-xl">
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
      </div>
    </div>
  );
}