import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import RequireAuth from "@/components/RequireAuth";
import Login from "@/pages/auth/Login";
import UnifiedLogin from "@/pages/auth/UnifiedLogin";
import Landing from "@/pages/landing/Landing";
import Signup from "@/pages/auth/Signup";
import ForgotPassword from "@/pages/auth/ForgotPassword";
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
        {/* The front door: both logins reachable from one place. */}
        <Route path="/" element={<Landing />} />

        {/* Two doors (auth-004): students AND teachers at /login (the
            unified door, role-first routing), admins at /admin/login. Both
            hit the same POST /auth/login through lib/api. */}
        <Route path="/login" element={<UnifiedLogin />} />
        <Route path="/admin/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/*
          auth-002: forgot-password is UI-only BY CONTRACT -- this page must
          never issue a network request. There is no backend endpoint and that
          is a recorded decision, not a gap.
        */}
        <Route path="/forgot-password" element={<ForgotPassword />} />

        {/* The welcome steps belong to SIGNUP. Guarded as student-only so a
            teacher or admin who types the URL is bounced to their own
            surface rather than being asked "who are you?" -- teachers are
            issued their account by an admin and never sign up (auth-004). */}
        <Route
          path="/onboarding/1"
          element={
            <RequireAuth role="student">
              <Onboarding1 />
            </RequireAuth>
          }
        />
        <Route
          path="/onboarding/2"
          element={
            <RequireAuth role="student">
              <Onboarding2 />
            </RequireAuth>
          }
        />

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
