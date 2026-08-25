import { type ReactNode } from "react"

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen w-full bg-background relative overflow-hidden flex flex-col md:flex-row">
      {/* Ambient background glow */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-15%] left-[-10%] w-[45%] h-[45%] rounded-full bg-tertiary/5 blur-[120px]" />
        <div className="absolute bottom-[-15%] right-[-10%] w-[50%] h-[50%] rounded-full bg-secondary/5 blur-[150px]" />
      </div>

      {/* Brand / illustration panel */}
      <div className="hidden md:flex md:w-1/2 relative z-10 flex-col justify-between p-12 border-r border-outline-variant/30">
        <span className="text-headline-sm text-on-surface font-semibold tracking-tight">
          Nocturnal Scholar
        </span>

        <div className="max-w-[24rem]">
          <p className="font-serif text-headline-lg text-on-surface leading-tight">
            Knowledge is the path,
            <br />
            not the peak.
          </p>
          <p className="text-on-surface-variant text-body-md mt-4">
            Curriculum-aligned, adaptive, and built to close the gaps —
            not just answer the question.
          </p>
        </div>

        <span className="text-label-sm text-on-surface-variant opacity-50">
          © 2026 Nocturnal Scholar
        </span>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-12 relative z-10">
        <div className="glass-card w-full max-w-[28rem] rounded-xl p-card-inner-padding md:p-10">
          {children}
        </div>
      </div>
    </div>
  )
}