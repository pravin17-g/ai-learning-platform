import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useApp } from './context/AppContext.jsx';
import Navbar from './components/Navbar.jsx';

import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import StudentProfile from './pages/StudentProfile.jsx';
import CareerGoals from './pages/CareerGoals.jsx';
import SkillAssessment from './pages/SkillAssessment.jsx';
import SkillGapAnalysis from './pages/SkillGapAnalysis.jsx';
import LearningRoadmap from './pages/LearningRoadmap.jsx';
import ProgressTracker from './pages/ProgressTracker.jsx';

// Pages only for logged-out visitors (Login, Register)
function PublicOnly() {
  const { isLoggedIn } = useApp();
  if (isLoggedIn) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

// Pages only for logged-in students (sidebar + page content)
function ProtectedLayout() {
  const { isLoggedIn } = useApp();
  if (!isLoggedIn) return <Navigate to="/login" replace />;
  return (
    <div className="app-shell">
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnly />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<StudentProfile />} />
        <Route path="/career" element={<CareerGoals />} />
        <Route path="/assessment" element={<SkillAssessment />} />
        <Route path="/gap-analysis" element={<SkillGapAnalysis />} />
        <Route path="/roadmap" element={<LearningRoadmap />} />
        <Route path="/progress" element={<ProgressTracker />} />
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}