import { useState, type ReactNode } from "react";

import {
  AlertTriangle,
  ArrowRight,
  Bell,
  Check,
  CheckCircle,
  Edit3,
  Info,
  LayoutDashboard,
  BookOpen,
  MessageCircle,
  Play,
  Search,
  Send,
  Settings,
  Sparkles,
  TrendingUp,
  User,
  ClipboardCheck,
  BarChart3,
  GraduationCap,
  Brain,
  ClipboardList,
  CalendarDays,
} from "lucide-react";

type DashboardSection =
  | "Dashboard"
  | "My Course"
  | "Diagnostic"
  | "My Gaps"
  | "Lessons"
  | "Practice"
  | "Ask Tutor"
  | "Assignments"
  | "Settings";

const navigation: { label: DashboardSection; icon: typeof LayoutDashboard }[] = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "My Course", icon: BookOpen },
  { label: "Diagnostic", icon: ClipboardCheck },
  { label: "My Gaps", icon: BarChart3 },
  { label: "Lessons", icon: GraduationCap },
  { label: "Practice", icon: Brain },
  { label: "Ask Tutor", icon: MessageCircle },
  { label: "Assignments", icon: ClipboardList },
];

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState<DashboardSection>("Dashboard");

  return (
    <div className="min-h-screen bg-background text-on-background">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-50 flex h-full w-[240px] flex-col bg-forest-green">
        <div className="mb-md mt-sm p-lg">
          <span className="font-sans text-3xl font-bold tracking-widest text-white uppercase">
            JOURNEY
          </span>
        </div>

        <nav className="flex flex-1 flex-col overflow-y-auto px-sm">
          <div className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.label}
                  aria-current={activeSection === item.label ? "page" : undefined}
                  className={`flex w-full items-center rounded-lg px-sm py-3 text-left text-xs font-bold tracking-wider uppercase transition-all ${
                    activeSection === item.label
                      ? "border-l-4 border-[#e5b045] bg-forest-light text-white"
                      : "text-white/70 hover:bg-forest-light hover:text-white"
                  }`}
                  onClick={() => setActiveSection(item.label)}
                  type="button"
                >
                  <Icon className="mr-sm h-5 w-5 shrink-0" />
                  {item.label}
                </button>
              );
            })}
          </div>

          <div className="flex-1" />

          {/* IMPORTANT:
              This is intentionally the Assignments-page illustration. */}
          <div className="mt-auto border-t border-white/10 pt-4">
            <button
              aria-current={activeSection === "Settings" ? "page" : undefined}
              className={`mb-2 flex w-full items-center rounded-lg px-sm py-3 text-xs font-bold tracking-wider uppercase transition-all ${
                activeSection === "Settings"
                  ? "border-l-4 border-[#e5b045] bg-forest-light text-white"
                  : "text-white/70 hover:bg-forest-light hover:text-white"
              }`}
              onClick={() => setActiveSection("Settings")}
              type="button"
            >
              <Settings className="mr-sm h-5 w-5" />
              Settings
            </button>
          </div>
        </nav>
      </aside>

      {/* Main application area */}
      <div className="w-full pl-[240px]">
        {/* Top header */}
        <header className="fixed left-[240px] right-0 top-0 z-40 flex h-16 items-center justify-between border-b border-outline-variant bg-surface/80 px-lg backdrop-blur-xl">
          <div className="flex w-96 items-center rounded-full bg-surface-container px-md py-xs">
            <Search className="mr-xs h-5 w-5 text-on-surface-variant" />
            <input
              type="text"
              placeholder="Search lessons, gaps..."
              className="w-full border-none bg-transparent text-body-sm outline-none"
            />
          </div>

          <div className="flex items-center gap-md">
            <button className="rounded-full p-xs text-on-surface-variant transition-colors hover:bg-surface-container">
              <Bell className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-sm border-l border-outline-variant pl-md">
              <div className="hidden text-right sm:block">
                <p className="font-headline-sm text-label-md leading-none font-bold text-on-surface">
                  Alex Rivera
                </p>
                <p className="text-label-sm text-on-surface-variant">
                  Grade 11 Student
                </p>
              </div>

              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1a3d34]">
                <User className="h-[18px] w-[18px] text-white" />
              </div>
            </div>
          </div>
        </header>

        {/* Page */}
        <main className="min-h-screen bg-background pt-16">
          <div className="flex w-full flex-col gap-lg p-lg">
            <div className={activeSection === "Dashboard" ? "" : "hidden"}>
            {/* Greeting */}
            <div className="mb-md flex flex-col gap-xs">
              <h1 className="font-display-lg text-headline-lg text-on-background">
                Good morning, Alex!
              </h1>
              <p className="text-body-md text-on-surface-variant">
                Here's your learning progress for Physics 101.
              </p>
            </div>

            {/* Stats */}
            <div className="mb-md grid grid-cols-1 gap-sm md:grid-cols-2 lg:grid-cols-4">
              <StatCard
                label="Open Gaps"
                value="4"
                icon={<AlertTriangle className="h-5 w-5 text-error" />}
              />

              <StatCard
                label="Lessons Completed"
                value="12"
                icon={<CheckCircle className="h-5 w-5 text-secondary" />}
              />

              <StatCard
                label="Practice Accuracy"
                value="88%"
                icon={<TrendingUp className="h-5 w-5 text-primary" />}
                highlighted
              />

              <StatCard
                label="Pending Assignments"
                value="2"
                icon={<ClipboardList className="h-5 w-5 text-outline" />}
              />
            </div>

            {/* Main content + AI Tutor */}
            <div className="grid grid-cols-1 gap-lg lg:grid-cols-12">
              <div className="flex flex-col gap-lg lg:col-span-8">
                {/* Up Next */}
                <section className="group relative overflow-hidden rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary to-transparent opacity-10 transition-opacity duration-500 group-hover:opacity-20" />

                  <div className="relative z-10 flex flex-col gap-md">
                    <div className="flex items-center justify-between">
                      <span className="rounded bg-surface-variant/50 px-xs py-base text-label-sm tracking-wider text-on-surface-variant uppercase">
                        Up Next
                      </span>

                      <span className="flex items-center gap-xs rounded-full bg-[#D6B34A] px-sm py-xs text-label-md text-on-surface">
                        <CheckCircle className="h-4 w-4" />
                        82% Syllabus Aligned
                      </span>
                    </div>

                    <div>
                      <h2 className="mb-xs text-headline-lg font-semibold text-on-surface">
                        Circular Motion
                      </h2>

                      <p className="max-w-2xl text-body-md text-on-surface-variant">
                        Dive into the mechanics of objects in uniform circular
                        motion. We'll cover centripetal acceleration, angular
                        velocity, and practical applications in planetary
                        orbits.
                      </p>
                    </div>

                    <div className="mt-sm flex items-center gap-md">
                      <button className="flex items-center gap-xs rounded-lg bg-primary px-lg py-sm text-body-md text-on-primary transition-colors hover:bg-primary/90">
                        <Play className="h-5 w-5" />
                        Resume Lesson
                      </button>

                      <div className="flex items-center gap-sm">
                        <div className="h-2 w-32 overflow-hidden rounded-full bg-surface-variant">
                          <div className="h-full w-[60%] rounded-full bg-secondary" />
                        </div>

                        <span className="text-label-sm text-on-surface-variant">
                          60% Complete
                        </span>
                      </div>
                    </div>
                  </div>
                </section>

                {/* My Gaps */}
                <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest shadow-sm">
                  <div className="flex items-center justify-between border-b border-outline-variant/20 p-md">
                    <h3 className="text-headline-sm font-semibold text-on-surface">
                      My Gaps
                    </h3>
                    <span className="text-label-sm text-on-surface-variant uppercase">
                      3 Identified Topics
                    </span>
                  </div>

                  <div>
                    <GapRow
                      title="Newton's Third Law"
                      description="Struggling with action-reaction pair identification."
                      highlighted
                    />

                    <GapRow
                      title="Friction & Force"
                      description="Difficulty distinguishing static vs. kinetic friction."
                    />

                    <GapRow
                      title="Work-Energy Theorem"
                      description="Low accuracy in practice problems involving non-conservative forces."
                    />
                  </div>
                </section>

                {/* Recent Activity */}
                <section className="rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm">
                  <h3 className="mb-md text-headline-sm font-semibold text-on-surface">
                    Recent Activity
                  </h3>

                  <div className="relative flex flex-col gap-md">
                    <div className="absolute bottom-4 left-4 top-4 w-px bg-outline-variant/30" />

                    <Activity
                      icon={<Check className="h-4 w-4" />}
                      iconClass="bg-secondary text-on-secondary"
                      title="Completed:"
                      activity="Kinematics Quiz"
                      detail="Score: 92% • 2 hours ago"
                    />

                    <Activity
                      icon={<Edit3 className="h-4 w-4" />}
                      iconClass="bg-surface-container-highest text-on-surface-variant"
                      title="Attempted:"
                      activity="Gravity Practice"
                      detail="15/20 Correct • Yesterday"
                    />
                  </div>
                </section>
              </div>

              {/* AI Tutor */}
              <section className="flex h-[800px] flex-col overflow-hidden rounded-xl border border-outline-variant/20 bg-surface-container-lowest shadow-lg lg:col-span-4">
                <div className="flex shrink-0 items-center gap-sm bg-primary p-sm text-on-primary">
                  <Sparkles className="h-5 w-5" />

                  <div>
                    <h3 className="text-body-md font-semibold">
                      AI Tutor
                    </h3>
                    <p className="text-label-sm opacity-80">
                      Physics 101 Assistant
                    </p>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto bg-surface-container-low p-md">
                  <div className="flex flex-col gap-md">
                    <TutorMessage user>
                      Explain centripetal force.
                    </TutorMessage>

                    <TutorMessage>
                      <p>
                        Centripetal force is the net force that acts on an
                        object to keep it moving along a circular path. It is
                        always directed towards the center of curvature of the
                        path.
                      </p>

                      <div className="mt-sm rounded bg-white/10 p-xs">
                        <span className="block text-label-sm opacity-70">
                          CITATION
                        </span>
                        <span className="text-body-sm font-medium">
                          Concepts of Physics, Vol 1, p.143
                        </span>
                      </div>

                      <span className="mt-sm inline-flex items-center gap-xs rounded bg-secondary-container px-xs py-base text-label-sm text-on-secondary-container">
                        <BookOpen className="h-3.5 w-3.5" />
                        Syllabus Aligned
                      </span>
                    </TutorMessage>

                    <TutorMessage user>
                      Can you solve question 5 from the homework?
                    </TutorMessage>

                    <div className="flex flex-col items-start">
                      <div className="max-w-[90%] rounded-2xl rounded-tl-sm border-l-4 border-primary bg-surface-variant p-sm shadow-sm">
                        <div className="flex items-center gap-xs text-label-md text-primary">
                          <Info className="h-4 w-4" />
                          ASSIGNMENT DETECTED
                        </div>

                        <p className="mt-xs text-body-sm">
                          I can't solve graded questions directly, but I can
                          offer a hint! Consider the conservation of energy
                          principle for this setup. Would you like me to
                          explain that concept?
                        </p>
                      </div>
                    </div>

                    <TutorMessage user>
                      What about string theory?
                    </TutorMessage>

                    <div className="flex items-start gap-sm">
                      <Info className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

                      <p className="rounded-2xl rounded-tl-sm border border-amber-400/50 bg-amber-50 p-sm text-body-sm text-amber-900 shadow-sm">
                        I don't have approved material on this topic yet. My
                        focus is strictly on your current syllabus.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="shrink-0 border-t border-outline-variant/20 bg-surface p-sm">
                  <div className="flex items-center rounded-full border border-outline-variant/30 bg-surface-container px-sm py-xs transition-colors focus-within:border-secondary">
                    <input
                      type="text"
                      placeholder="Ask a question..."
                      className="w-full bg-transparent px-sm py-xs text-body-md text-on-surface outline-none placeholder:text-on-surface-variant/60"
                    />

                    <button className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#D6B34A] text-[#1b1c17] transition-colors hover:bg-[#D6B34A]/90">
                      <Send className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </section>
            </div>
            </div>
            {activeSection !== "Dashboard" && <DashboardSectionView section={activeSection} />}
          </div>
        </main>
      </div>
    </div>
  );
}

function DashboardSectionView({ section }: { section: Exclude<DashboardSection, "Dashboard"> }) {
  const content: Record<Exclude<DashboardSection, "Dashboard">, { title: string; description: string; items: { title: string; detail: string; action: string }[] }> = {
    "My Course": {
      title: "My Course",
      description: "Your Physics 101 syllabus and learning progress.",
      items: [
        { title: "Physics 101", detail: "12 of 18 lessons completed", action: "Continue course" },
        { title: "Course resources", detail: "4 approved books and reference materials", action: "View resources" },
      ],
    },
    Diagnostic: {
      title: "Diagnostic",
      description: "Find prerequisite gaps and build your learning path.",
      items: [
        { title: "Prerequisite diagnostic", detail: "A quick check of your current understanding", action: "Start diagnostic" },
        { title: "Latest result", detail: "3 concepts need another look", action: "Review result" },
      ],
    },
    "My Gaps": {
      title: "My Gaps",
      description: "Topics to revisit based on your diagnostic and practice work.",
      items: [
        { title: "Newton's Third Law", detail: "Action-reaction pair identification", action: "Start lesson" },
        { title: "Friction & Force", detail: "Static versus kinetic friction", action: "Start lesson" },
        { title: "Work-Energy Theorem", detail: "Non-conservative force problems", action: "Start lesson" },
      ],
    },
    Lessons: {
      title: "Lessons",
      description: "Continue learning with syllabus-aligned lessons.",
      items: [
        { title: "Circular Motion", detail: "60% complete · 18 minutes remaining", action: "Resume lesson" },
        { title: "Gravitation", detail: "Next lesson · Ready to begin", action: "Start lesson" },
      ],
    },
    Practice: {
      title: "Practice",
      description: "Build confidence with targeted questions.",
      items: [
        { title: "Newton's Laws practice", detail: "10 questions · Focus: identified gaps", action: "Start practice" },
        { title: "Gravity practice", detail: "15 of 20 correct", action: "Review attempt" },
      ],
    },
    "Ask Tutor": {
      title: "Ask Tutor",
      description: "Ask about approved course material and receive cited explanations.",
      items: [
        { title: "Continue your conversation", detail: "Your tutor is ready to explain Physics 101", action: "Open tutor" },
        { title: "Suggested question", detail: "How does centripetal acceleration work?", action: "Ask this" },
      ],
    },
    Assignments: {
      title: "Assignments",
      description: "Track your upcoming and completed coursework.",
      items: [
        { title: "Circular motion worksheet", detail: "Due tomorrow · Not started", action: "View assignment" },
        { title: "Kinematics quiz", detail: "Completed · Score: 92%", action: "Review score" },
      ],
    },
    Settings: {
      title: "Settings",
      description: "Manage your profile and learning preferences.",
      items: [
        { title: "Profile", detail: "Alex Rivera · Grade 11 Student", action: "Edit profile" },
        { title: "Language", detail: "English · Hindi available", action: "Change language" },
      ],
    },
  };

  const current = content[section];

  return (
    <section className="w-full max-w-4xl">
      <div className="mb-lg">
        <p className="text-label-sm font-bold tracking-widest text-secondary uppercase">Student workspace</p>
        <h1 className="mt-xs text-headline-lg font-semibold text-on-background">{current.title}</h1>
        <p className="mt-xs text-body-md text-on-surface-variant">{current.description}</p>
      </div>
      <div className="grid gap-md md:grid-cols-2">
        {current.items.map((item) => (
          <article className="border border-outline-variant/30 bg-surface-container-lowest p-lg shadow-sm" key={item.title}>
            <h2 className="text-headline-sm font-semibold text-on-surface">{item.title}</h2>
            <p className="mt-sm text-body-md text-on-surface-variant">{item.detail}</p>
            <button className="mt-lg flex items-center gap-xs bg-primary px-md py-sm text-body-sm font-semibold text-on-primary transition-colors hover:bg-secondary" type="button">
              {item.action}
              <ArrowRight className="h-4 w-4" />
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

function StatCard({
  label,
  value,
  icon,
  highlighted = false,
}: {
  label: string;
  value: string;
  icon: ReactNode;
  highlighted?: boolean;
}) {
  return (
    <div
      className={`relative flex flex-col gap-sm overflow-hidden rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-md shadow-sm ${
        highlighted ? "" : ""
      }`}
    >
      {highlighted && (
        <div className="absolute inset-0 bg-gradient-to-br from-primary to-transparent opacity-10" />
      )}

      <div className="relative z-10 flex items-center justify-between">
        <span className="text-label-sm text-on-surface-variant uppercase">
          {label}
        </span>
        {icon}
      </div>

      <div
        className={`relative z-10 text-display-lg ${
          highlighted ? "text-primary" : "text-on-surface"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function GapRow({
  title,
  description,
  highlighted = false,
}: {
  title: string;
  description: string;
  highlighted?: boolean;
}) {
  return (
    <div className="group flex items-center justify-between border-b border-outline-variant/10 p-md transition-colors hover:bg-surface-container-low last:border-b-0">
      <div className="flex items-start gap-sm">
        <div className="mt-xs flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-error-container text-on-error-container">
          <AlertTriangle className="h-[18px] w-[18px]" />
        </div>

        <div>
          <h4 className="text-body-lg font-semibold text-on-surface">
            {title}
          </h4>
          <p className="text-body-sm text-on-surface-variant">
            {description}
          </p>
        </div>
      </div>

      <button
        className={`flex items-center gap-xs rounded px-sm py-xs text-body-sm transition-opacity ${
          highlighted
            ? "bg-[#D6B34A] text-[#1b1c17]"
            : "bg-surface-container-highest text-on-surface"
        } opacity-0 group-hover:opacity-100`}
      >
        Start Lesson
        <ArrowRight className="h-4 w-4" />
      </button>
    </div>
  );
}

function Activity({
  icon,
  iconClass,
  title,
  activity,
  detail,
}: {
  icon: React.ReactNode;
  iconClass: string;
  title: string;
  activity: string;
  detail: string;
}) {
  return (
    <div className="relative z-10 flex items-start gap-md">
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${iconClass}`}
      >
        {icon}
      </div>

      <div>
        <p className="text-body-md">
          <span className="font-semibold">{title}</span> {activity}
        </p>
        <p className="text-body-sm text-on-surface-variant">{detail}</p>
      </div>
    </div>
  );
}

function TutorMessage({
  children,
  user = false,
}: {
  children: ReactNode;
  user?: boolean;
}) {
  return (
    <div className={`flex flex-col gap-xs ${user ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[90%] rounded-2xl px-md py-sm shadow-sm ${
          user
            ? "rounded-tr-sm border border-outline-variant/40 bg-surface text-on-surface"
            : "rounded-tl-sm bg-secondary text-on-secondary"
        }`}
      >
        {typeof children === "string" ? (
          <p className="text-body-md">{children}</p>
        ) : (
          <div className="text-body-md">{children}</div>
        )}
      </div>

      {user && (
        <span className="mr-xs text-label-sm text-on-surface-variant">
          10:42 AM
        </span>
      )}
    </div>
  );
}