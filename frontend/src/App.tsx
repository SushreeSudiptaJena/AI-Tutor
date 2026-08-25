import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "@/pages/admin/Login";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import Onboarding1 from "@/pages/onboarding/Onboarding1";
import Onboarding2 from "@/pages/onboarding/Onboarding2";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route path="/onboarding/1" element={<Onboarding1 />} />
        <Route path="/onboarding/2" element={<Onboarding2 />} />

        <Route path="/admin" element={<AdminDashboard />} />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}