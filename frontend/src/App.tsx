import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Login from "@/pages/admin/Login";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import Onboarding1 from "@/pages/onboarding/Onboarding1";
import Onboarding2 from "@/pages/onboarding/Onboarding2";
import StudentLogin from "@/pages/auth/Login";
import OnboardingCourse from "@/pages/student/OnboardingCourse";
import OnboardingDiagnostic from "@/pages/student/OnboardingDiagnostic";
import Dashboard from "@/pages/student/Dashboard";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<StudentLogin />} />
        <Route path="/admin/login" element={<Login />} />
        <Route path="/onboarding/1" element={<Onboarding1 />} />
        <Route path="/onboarding/2" element={<Onboarding2 />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/onboarding/course" element={<OnboardingCourse />} />
        <Route path="/onboarding/diagnostic" element={<OnboardingDiagnostic />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}