import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "@/pages/admin/Login";
import AdminDashboard from "@/pages/admin/AdminDashboard";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}