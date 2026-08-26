import { useState } from "react"
import { useNavigate } from "react-router-dom"

const options = [
  { id: "homework", label: "Homework help", icon: "book" },
  { id: "exam", label: "Exam preparation", icon: "school" },
  { id: "coding", label: "Coding / Technical learning", icon: "code" },
  { id: "creative", label: "Creative / Design learning", icon: "palette" },
  { id: "general", label: "General knowledge / Curiosity", icon: "public" },
  { id: "other", label: "Other", icon: "more_horiz" },
]

export default function WhatDoYouUse() {
  const navigate = useNavigate()

  // These two are selected initially, matching your Stitch design.
  const [selected, setSelected] = useState<string[]>([
    "coding",
    "general",
  ])

  function toggleOption(id: string) {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    )
  }

  function handleContinue() {
    localStorage.setItem(
      "onboardingUses",
      JSON.stringify(selected)
    )

    const role = localStorage.getItem("onboardingRole")

    if (role === "teacher") {
      navigate("/teacher")
    } else if (role === "student") {
      navigate("/student")
    } else if (role === "other") {
      navigate("/student")
    } else {
      navigate("/student")
    }
  }

  function handleSkip() {
    navigate("/student")
  }

  return (
    <div className="min-h-screen bg-[#121414] text-[#e2e2e2] flex flex-col items-center justify-center font-sans overflow-x-hidden relative">

      {/* Decorative background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[#9dd75b]/5 blur-[120px]" />

        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#9dd75b]/5 blur-[150px]" />
      </div>

      {/* Main content */}
      <main className="w-full max-w-4xl px-8 py-16 flex flex-col items-center justify-center flex-grow z-10 relative">

        {/* Step indicator */}
        <div className="mb-8">
          <span className="text-[#c3c7ca] font-semibold text-[14px] tracking-widest uppercase">
            Step 2 of 2
          </span>
        </div>

        {/* Heading */}
        <div className="text-center mb-12 max-w-2xl">
          <h1 className="text-[40px] md:text-[48px] leading-tight font-bold text-[#bbc9d1] tracking-tight mb-4">
            What will you use this for?
          </h1>

          <p className="text-[18px] leading-7 text-[#c3c7ca]">
            Select all that apply to help us tailor your AI-assisted
            research environment.
          </p>
        </div>

        {/* Selection grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full mb-40">

          {options.map((option) => {
            const isSelected = selected.includes(option.id)

            return (
              <button
                key={option.id}
                type="button"
                aria-pressed={isSelected}
                onClick={() => toggleOption(option.id)}
                className={`
                  rounded-xl
                  p-6
                  flex flex-col
                  items-center
                  justify-center
                  gap-4
                  text-center
                  cursor-pointer
                  h-48
                  border
                  backdrop-blur-[16px]
                  transition-all duration-300
                  focus:outline-none
                  focus:ring-2
                  focus:ring-[#9dd75b]

                  ${
                    isSelected
                      ? `
                        bg-[rgba(184,244,115,0.08)]
                        border-[#9dd75b]
                        shadow-[0_0_30px_rgba(184,244,115,0.15)]
                      `
                      : `
                        bg-[rgba(255,255,255,0.03)]
                        border-[rgba(255,255,255,0.08)]
                        hover:bg-[rgba(255,255,255,0.06)]
                        hover:border-[rgba(255,255,255,0.15)]
                      `
                  }
                `}
              >
                <span
                  className={`
                    material-symbols-outlined
                    text-4xl
                    transition-colors

                    ${
                      isSelected
                        ? "text-[#9dd75b]"
                        : "text-[#c3c7ca]"
                    }
                  `}
                  style={{
                    fontVariationSettings: isSelected
                      ? "'FILL' 1"
                      : "'FILL' 0",
                  }}
                >
                  {option.icon}
                </span>

                <span className="text-[20px] leading-7 font-medium text-[#e2e2e2]">
                  {option.label}
                </span>
              </button>
            )
          })}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-transparent fixed bottom-0 w-full flex flex-col items-center justify-center pb-8 gap-2 z-20">

        {/* Continue */}
        <button
          type="button"
          onClick={handleContinue}
          className="
            bg-gradient-to-br
            from-[#9dd75b]
            to-[#70a62f]
            text-[#1e3700]
            font-semibold
            text-[14px]
            px-8
            py-3
            rounded-full
            mb-4
            w-64
            text-center
            flex
            justify-center
            items-center
            gap-2
            shadow-[0_4px_20px_rgba(184,244,115,0.3)]
            transition-all
            duration-300
            hover:-translate-y-0.5
            hover:shadow-[0_6px_25px_rgba(184,244,115,0.5)]
          "
        >
          Continue

          <span className="material-symbols-outlined text-xl">
            arrow_forward
          </span>
        </button>

        {/* Skip */}
        <button
          type="button"
          onClick={handleSkip}
          className="
            text-[#c3c7ca]
            hover:text-[#e2e2e2]
            text-[12px]
            font-medium
            transition-colors
            underline
            underline-offset-4
          "
        >
          Skip for now
        </button>

        {/* Copyright */}
        <span className="text-[#c3c7ca] text-[12px] mt-4 opacity-50">
          © 2026 Journey.
        </span>
      </footer>
    </div>
  )
}