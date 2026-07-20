import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import Login from './pages/Login';
import Onboarding from './pages/Onboarding';
import Home from './pages/Home';
import NewDilemma from './pages/NewDilemma';
import CardChat from './pages/CardChat';
import Memories from './pages/Memories';
import InsightGallery from './pages/InsightGallery';
import Community from './pages/Community';
import SettingsPage from './pages/Settings';
import './styles/global.css';

const THEME_ACCENTS = {
  default: '#4A7DFF',
  neutral: '#1a1a2e',
  emerald: '#10b981',
  rose: '#ec4899',
  amber: '#f59e0b',
  violet: '#8b5cf6',
};

export function applyTheme(theme) {
  const accent = THEME_ACCENTS[theme] || THEME_ACCENTS.default;
  document.documentElement.style.setProperty('--accent', accent);
  document.documentElement.style.setProperty('--accent-light', accent + '14');
  document.documentElement.style.setProperty('--bubble-user', accent);
}

function ProtectedRoute({ children }) {
  const uid = localStorage.getItem('uid');
  if (!uid) return <Navigate to="/" replace />;
  return children;
}

function App() {
  useEffect(() => {
    const theme = localStorage.getItem('theme') || 'default';
    applyTheme(theme);
  }, []);

  return (
    <BrowserRouter>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/register" element={<Onboarding />} />
          <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="/new" element={<ProtectedRoute><NewDilemma /></ProtectedRoute>} />
          <Route path="/card/:cardId" element={<ProtectedRoute><CardChat /></ProtectedRoute>} />
          <Route path="/memories" element={<ProtectedRoute><Memories /></ProtectedRoute>} />
          <Route path="/insights" element={<ProtectedRoute><InsightGallery /></ProtectedRoute>} />
          <Route path="/community" element={<ProtectedRoute><Community /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
