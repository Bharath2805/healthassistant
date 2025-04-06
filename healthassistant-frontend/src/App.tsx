// src/App.tsx
import { Routes, Route, Navigate } from "react-router-dom";

// Pages
import Home from "./pages/Home";
import Chat from "./pages/Chat";
import ChatWithSymptoms from "./pages/ChatWithSymptoms";
import Doctors from "./pages/Doctors";
import ImageAnalysis from "./pages/ImageAnalysis";

import AuthPage from "./pages/AuthPage";
import GoogleAuthSuccess from "./pages/GoogleAuthSuccess";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Reminders from "./pages/Reminders"; // ✅ Import your Reminders page

function App() {
  return (
    <Routes>
      {/* Auth */}
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/login" element={<Navigate to="/auth" replace />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/google-auth-success" element={<GoogleAuthSuccess />} />

      {/* Public Pages */}
      <Route path="/" element={<Home />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/symptoms" element={<ChatWithSymptoms />} />
      <Route path="/doctors" element={<Doctors />} />
      <Route path="/images" element={<ImageAnalysis />} />
      
      <Route path="/reminders" element={<Reminders />} /> {/* ✅ Now included */}

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/auth" replace />} />
    </Routes>
  );
}

export default App;
