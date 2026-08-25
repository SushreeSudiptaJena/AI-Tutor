import { MouseEvent, useState } from "react";
import AssignmentsLibraryHighContrast from "./AssignmentsLibraryHighContrast";
import AttendanceTrackerHighContrast from "./AttendanceTrackerHighContrast";
import BeforeAfterTrackingHighContrast from "./BeforeAfterTrackingHighContrast";
import ContentVerificationHighContrast from "./ContentVerificationHighContrast";
import DashboardOverviewHighContrast from "./DashboardOverviewHighContrast";
import LessonPlansLibraryHighContrast from "./LessonPlansLibraryHighContrast";
import MisconceptionHeatmapHighContrast from "./MisconceptionHeatmapHighContrast";
import MyClassesHighContrast from "./MyClassesHighContrast";
import PrerequisiteGapMapHighContrast from "./PrerequisiteGapMapHighContrast";
import ReasoningPathBreakdownHighContrast from "./ReasoningPathBreakdownHighContrast";
import SettingsHighContrast from "./SettingsHighContrast";
import StudentDirectoryHighContrast from "./StudentDirectoryHighContrast";
import SuggestedReteachHighContrast from "./SuggestedReteachHighContrast";
import UncertaintyFlagsHighContrast from "./UncertaintyFlagsHighContrast";

const pages = {
  dashboard: DashboardOverviewHighContrast,
  "my-classes": MyClassesHighContrast,
  students: StudentDirectoryHighContrast,
  attendance: AttendanceTrackerHighContrast,
  "lesson-plans": LessonPlansLibraryHighContrast,
  assignments: AssignmentsLibraryHighContrast,
  "misconception-heatmap": MisconceptionHeatmapHighContrast,
  "reasoning-path-breakdown": ReasoningPathBreakdownHighContrast,
  "gap-map": PrerequisiteGapMapHighContrast,
  "uncertainty-flags": UncertaintyFlagsHighContrast,
  tracking: BeforeAfterTrackingHighContrast,
  "suggested-reteach": SuggestedReteachHighContrast,
  "content-verification": ContentVerificationHighContrast,
  settings: SettingsHighContrast,
};

type TeacherPage = keyof typeof pages;

export default function TeacherDashboard() {
  const [activePage, setActivePage] = useState<TeacherPage>("dashboard");
  const ActivePage = pages[activePage];

  function handleNavigation(event: MouseEvent<HTMLDivElement>) {
    const link = (event.target as HTMLElement).closest<HTMLElement>("[data-path]");
    const page = link?.dataset.path as TeacherPage | undefined;

    if (!page || !(page in pages)) return;

    event.preventDefault();
    setActivePage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    /* teacher-scope carries the teacher palette (see index.css): the merged
       @theme serves three design systems now, and a shared token name must
       resolve to the definition made for THIS surface, not the last one. */
    <div className="teacher-scope" onClick={handleNavigation}>
      <ActivePage />
    </div>
  );
}
