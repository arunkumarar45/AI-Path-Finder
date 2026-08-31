import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { useState, createContext, useContext } from 'react';
import {
  LayoutDashboard, Map, MessageCircle, BarChart3, Star,
  ChevronRight, Sparkles
} from 'lucide-react';

import { learnerApi } from './lib/api';
import Dashboard from './pages/Dashboard';
import Roadmap from './pages/Roadmap';
import SkillGap from './pages/SkillGap';
import AIAssistant from './pages/AIAssistant';
import Assessments from './pages/Assessments';
import Onboarding from './pages/Onboarding';

import './index.css';

// ── Global state ─────────────────────────────────────────────────────────────

interface AppContextType {
  learnerId: number | null;
  setLearnerId: (id: number) => void;
}

const AppContext = createContext<AppContextType>({ learnerId: null, setLearnerId: () => {} });
export const useApp = () => useContext(AppContext);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

// ── Sidebar ───────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/roadmap', label: 'Learning Roadmap', icon: Map },
  { path: '/skill-gaps', label: 'Skill Analysis', icon: BarChart3 },
  { path: '/assistant', label: 'AI Mentor', icon: MessageCircle },
  { path: '/assessments', label: 'Assessments', icon: Star },
];

function Sidebar({ learnerName, progress }: { learnerName: string; progress: number }) {
  const location = useLocation();

  return (
    <nav className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🧠</div>
        <div>
          <div className="sidebar-logo-text">AI Path Finder</div>
          <div className="sidebar-logo-sub">Learning Recommender</div>
        </div>
      </div>

      {/* Learner mini card */}
      <div style={{
        padding: '10px 12px',
        marginBottom: '8px',
        background: 'rgba(99,102,241,0.08)',
        border: '1px solid rgba(99,102,241,0.2)',
        borderRadius: '10px',
      }}>
        <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Learner</div>
        <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text)', marginBottom: '8px' }}>
          {learnerName}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="progress-bar" style={{ flex: 1 }}>
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-primary-light)', fontWeight: 600 }}>
            {progress.toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="nav-section-label">Navigation</div>

      {NAV_ITEMS.map(item => {
        const Icon = item.icon;
        const active = location.pathname === item.path;
        return (
          <Link key={item.path} to={item.path} className={`nav-item ${active ? 'active' : ''}`}>
            <span className="nav-item-icon"><Icon size={18} /></span>
            {item.label}
            {active && <ChevronRight size={14} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
          </Link>
        );
      })}

      <div style={{ flex: 1 }} />

      {/* Bottom badge */}
      <div style={{
        padding: '10px 12px',
        background: 'rgba(20,184,166,0.08)',
        border: '1px solid rgba(20,184,166,0.2)',
        borderRadius: '10px',
        textAlign: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center', marginBottom: '4px' }}>
          <Sparkles size={14} color="#14b8a6" />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-secondary)' }}>AI-Powered</span>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Adapts to your learning style
        </div>
      </div>
    </nav>
  );
}

// ── Layout (wraps pages) ──────────────────────────────────────────────────────

function AppLayout({ children }: { children: React.ReactNode }) {
  const { learnerId } = useApp();
  const { data } = useQuery({
    queryKey: ['learner', learnerId],
    queryFn: () => learnerApi.get(learnerId!).then(r => r.data),
    enabled: !!learnerId,
  });

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar
        learnerName={data?.name || 'Loading...'}
        progress={data?.overall_progress || 0}
      />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

// ── Root app ──────────────────────────────────────────────────────────────────

function AppRoutes() {
  const { learnerId, setLearnerId } = useApp();

  if (!learnerId) {
    return <Onboarding onComplete={setLearnerId} />;
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard learnerId={learnerId} />} />
        <Route path="/roadmap" element={<Roadmap learnerId={learnerId} />} />
        <Route path="/skill-gaps" element={<SkillGap learnerId={learnerId} />} />
        <Route path="/assistant" element={<AIAssistant learnerId={learnerId} />} />
        <Route path="/assessments" element={<Assessments learnerId={learnerId} />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppLayout>
  );
}

export default function App() {
  const [learnerId, setLearnerId] = useState<number | null>(null);

  return (
    <QueryClientProvider client={queryClient}>
      <AppContext.Provider value={{ learnerId, setLearnerId }}>
        <Router>
          <AppRoutes />
        </Router>
      </AppContext.Provider>
    </QueryClientProvider>
  );
}
