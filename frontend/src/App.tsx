import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Landing from "@/pages/landing/Landing";

import Login from "@/pages/admin/Login";
import AdminDashboard from "@/pages/admin/AdminDashboard";

import Onboarding1 from "@/pages/onboarding/Onboarding1";
import Onboarding2 from "@/pages/onboarding/Onboarding2";

import StudentLogin from "@/pages/auth/Login";

import OnboardingCourse from "@/pages/student/OnboardingCourse";
import OnboardingDiagnostic from "@/pages/student/OnboardingDiagnostic";
import Dashboard from "@/pages/student/Dashboard";

import TeacherDashboard from "@/pages/teacher/TeacherDashboard";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing */}
        <Route path="/" element={<Landing />} />

        {/* Authentication */}
        <Route path="/login" element={<StudentLogin />} />
        <Route path="/admin/login" element={<Login />} />

        {/* Existing onboarding */}
        <Route path="/onboarding/1" element={<Onboarding1 />} />
        <Route path="/onboarding/2" element={<Onboarding2 />} />

        {/* Student */}
        <Route
          path="/onboarding/course"
          element={<OnboardingCourse />}
        />

        <Route
          path="/onboarding/diagnostic"
          element={<OnboardingDiagnostic />}
        />

        <Route
          path="/dashboard"
          element={<Dashboard />}
        />

        {/* Teacher */}
        <Route
          path="/teacher"
          element={<TeacherDashboard />}
        />

        {/* Admin */}
        <Route
          path="/admin"
          element={<AdminDashboard />}
        />

        {/* Unknown routes */}
        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}