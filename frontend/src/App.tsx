import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import RequireAuth from "@/components/RequireAuth";
import Login from "@/pages/auth/Login";
import StudentLogin from "@/pages/auth/StudentLogin";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import Onboarding1 from "@/pages/onboarding/Onboarding1";
import Onboarding2 from "@/pages/onboarding/Onboarding2";
import OnboardingCourse from "@/pages/student/OnboardingCourse";
import OnboardingDiagnostic from "@/pages/student/OnboardingDiagnostic";
import Dashboard from "@/pages/student/Dashboard";
import TeacherDashboard from "@/pages/teacher/TeacherDashboard";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Two doors: students enter at /login (Anu's screen, routes by
            course_id), admins at /admin/login. Both hit the same
            POST /auth/login through lib/api. */}
        <Route path="/login" element={<StudentLogin />} />
        <Route path="/admin/login" element={<Login />} />

        <Route path="/onboarding/1" element={<Onboarding1 />} />
        <Route path="/onboarding/2" element={<Onboarding2 />} />

        {/* The student flow past login. Guarded server-side via /auth/me:
            these pages call student-only endpoints. */}
        <Route
          path="/onboarding/course"
          element={
            <RequireAuth role="student">
              <OnboardingCourse />
            </RequireAuth>
          }
        />
        <Route
          path="/onboarding/diagnostic"
          element={
            <RequireAuth role="student">
              <OnboardingDiagnostic />
            </RequireAuth>
          }
        />
        <Route
          path="/dashboard"
          element={
            <RequireAuth role="student">
              <Dashboard />
            </RequireAuth>
          }
        />

        {/*
          Guarded against the SERVER's answer rather than localStorage: every
          route inside /admin is admin-only in the backend, so an
          unauthenticated or non-admin visitor would otherwise be shown a full
          dashboard whose every panel then fails with 401/403.
        */}
        <Route
          path="/admin"
          element={
            <RequireAuth role="admin">
              <AdminDashboard />
            </RequireAuth>
          }
        />

        {/* 111d770's teacher surface, under the same server-verified guard
            as the other two roles: /teacher/* endpoints are teacher-only. */}
        <Route
          path="/teacher"
          element={
            <RequireAuth role="teacher">
              <TeacherDashboard />
            </RequireAuth>
          }
        />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
