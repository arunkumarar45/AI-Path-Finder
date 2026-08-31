import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardApi, roadmapApi } from '../lib/api';
import { Link } from 'react-router-dom';
import {
  TrendingUp, Target, Clock, Zap, Award, ChevronRight,
  Sparkles, CheckCircle2, Circle, Loader2, Flame,
  Map
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface DashboardProps {
  learnerId: number;
}

function CircularProgress({ value, size = 120 }: { value: number; size?: number }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="circular-progress" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="var(--color-surface-3)" strokeWidth={10}
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="url(#grad)" strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transform: 'rotate(-90deg)', transformOrigin: 'center', transition: 'stroke-dashoffset 1s ease' }}
        />
        <defs>
          <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>
      </svg>
      <div className="circular-progress-text" style={{ fontSize: size * 0.18 }}>
        {Math.round(value)}%
      </div>
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  'ON_TRACK': 'var(--color-success)',
  'AHEAD_OF_SCHEDULE': 'var(--color-primary-light)',
  'AT_RISK': 'var(--color-warning)',
};

const STATUS_LABELS: Record<string, string> = {
  'ON_TRACK': '✅ On Track',
  'AHEAD_OF_SCHEDULE': '🚀 Ahead of Schedule',
  'AT_RISK': '⚠️ At Risk',
};


export default function Dashboard({ learnerId }: DashboardProps) {
  const qc = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', learnerId],
    queryFn: () => dashboardApi.get(learnerId).then(r => r.data),
    refetchInterval: 60_000,
  });

  const completeMutation = useMutation({
    mutationFn: (itemId: number) => roadmapApi.updateItemStatus(itemId, 'COMPLETED'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dashboard', learnerId] });
      qc.invalidateQueries({ queryKey: ['roadmap', learnerId] });
    },
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader2 size={40} color="var(--color-primary)" style={{ animation: 'spin 1s linear infinite' }} />
          <div style={{ marginTop: '1rem', color: 'var(--color-text-secondary)' }}>Loading your dashboard...</div>
          <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--color-text-secondary)' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚠️</div>
        <div>Failed to load dashboard. Please refresh the page.</div>
      </div>
    );
  }

  const skillChart = data.skill_chart_data?.slice(0, 6).map((s: any) => ({
    name: s.skill.length > 10 ? s.skill.substring(0, 10) + '...' : s.skill,
    current: s.current,
    target: s.target,
    gap: s.gap * 100,
    priority: s.priority,
  })) || [];

  return (
    <div className="fade-in">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Welcome back, {data.learner?.name?.split(' ')[0]} 👋
          </h1>
          <p className="page-subtitle">
            Goal: <strong style={{ color: 'var(--color-primary-light)' }}>{data.learner?.career_goal}</strong>
            {' '}·{' '}
            <span style={{ color: STATUS_COLORS[data.deadline_status] || 'var(--color-success)' }}>
              {STATUS_LABELS[data.deadline_status] || '✅ On Track'}
            </span>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/roadmap" className="btn btn-primary btn-sm">
            <Map size={14} /> View Roadmap <ChevronRight size={14} />
          </Link>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          {
            icon: <TrendingUp size={22} color="#6366f1" />,
            bg: 'rgba(99,102,241,0.1)',
            value: `${data.overall_progress?.toFixed(0)}%`,
            label: 'Overall Progress',
          },
          {
            icon: <Zap size={22} color="#14b8a6" />,
            bg: 'rgba(20,184,166,0.1)',
            value: data.skills_developed,
            label: 'Skills Developed',
          },
          {
            icon: <Clock size={22} color="#f59e0b" />,
            bg: 'rgba(245,158,11,0.1)',
            value: `${data.total_hours_learned}h`,
            label: 'Hours Learned',
          },
          {
            icon: <Flame size={22} color="#ef4444" />,
            bg: 'rgba(239,68,68,0.1)',
            value: data.streak,
            label: 'Day Streak 🔥',
          },
        ].map((stat, i) => (
          <div key={i} className="stat-card">
            <div className="stat-icon" style={{ background: stat.bg }}>{stat.icon}</div>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Progress overview */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <CircularProgress value={data.overall_progress || 0} />
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Learning Progress</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', width: '100px' }}>Phases</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>
                    {data.current_phase} / {data.total_phases}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', width: '100px' }}>Milestones</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>
                    {data.milestones_completed} / {data.milestones_total}
                    {data.milestones_completed === data.milestones_total && data.milestones_total > 0 &&
                      <span style={{ marginLeft: '8px' }}>🏆</span>}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', width: '100px' }}>Roadmap</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>
                    {data.roadmap_summary?.completed_items} / {data.roadmap_summary?.total_items} items
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', width: '100px' }}>ETA</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-primary-light)' }}>
                    {data.roadmap_summary?.estimated_completion}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Skill chart */}
          <div>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Skill Proficiency (Current vs Target)
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={skillChart} barGap={4}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 5]} tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)', borderRadius: '8px', fontSize: '12px' }}
                  labelStyle={{ color: 'var(--color-text)' }}
                />
                <Bar dataKey="current" name="Current" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="target" name="Target" fill="rgba(99,102,241,0.2)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sidebar: Next Best Action + AI Insights */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Next Best Action */}
          {data.next_best_action && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08))',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Zap size={16} color="var(--color-primary-light)" />
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-primary-light)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Next Best Action
                </span>
              </div>
              <div style={{ fontSize: '15px', fontWeight: 700, marginBottom: '8px', lineHeight: 1.3 }}>
                {data.next_best_action.action}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '12px', lineHeight: 1.5 }}>
                {data.next_best_action.reason}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                  ⏱️ ~{Math.round((data.next_best_action.estimated_time || 120) / 60)}h
                </span>
                <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>
                  {data.next_best_action.impact?.split(' — ')[0]}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                <div style={{
                  flex: 1, height: 4, borderRadius: 2,
                  background: 'var(--color-surface-3)',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${(data.next_best_action.confidence || 0.8) * 100}%`,
                    height: '100%',
                    background: 'var(--gradient-primary)',
                    borderRadius: 2,
                  }} />
                </div>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  {Math.round((data.next_best_action.confidence || 0.8) * 100)}% match
                </span>
              </div>
              {data.next_best_action.roadmap_item_id && (
                <button
                  className="btn btn-primary btn-sm"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={() => completeMutation.mutate(data.next_best_action.roadmap_item_id)}
                  disabled={completeMutation.isPending}
                >
                  {completeMutation.isPending ? <Loader2 size={14} /> : <CheckCircle2 size={14} />}
                  Mark Complete
                </button>
              )}
            </div>
          )}

          {/* AI Insights */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
              <Sparkles size={16} color="var(--color-secondary)" />
              <h3 style={{ fontSize: '14px', fontWeight: 700 }}>AI Insights</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(data.ai_insights || []).map((insight: string, i: number) => (
                <div key={i} className="insight-card">
                  <div style={{ fontSize: '18px', flexShrink: 0 }}>
                    {['💡', '🎯', '📈', '⚡'][i % 4]}
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                    {insight}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Critical Gaps */}
      {data.skill_gap_summary?.critical_count > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Target size={18} color="var(--color-danger)" />
              <h3 style={{ fontSize: '15px', fontWeight: 700 }}>Critical Skill Gaps</h3>
              <span className="badge badge-critical">{data.skill_gap_summary.critical_count} gaps</span>
            </div>
            <Link to="/skill-gaps" className="btn btn-ghost btn-sm">
              Full Analysis <ChevronRight size={14} />
            </Link>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {(data.skill_gap_summary?.top_critical_gaps || []).map((skill: string) => (
              <div key={skill} style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '6px 12px',
                background: 'rgba(239,68,68,0.08)',
                border: '1px solid rgba(239,68,68,0.2)',
                borderRadius: '20px',
                fontSize: '13px',
                color: 'var(--color-danger)',
                fontWeight: 500,
              }}>
                <Circle size={8} fill="currentColor" />
                {skill}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {data.recent_activity?.length > 0 && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
            <Award size={18} color="var(--color-success)" />
            <h3 style={{ fontSize: '15px', fontWeight: 700 }}>Recent Completions</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {data.recent_activity.slice(0, 4).map((activity: any, i: number) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'rgba(34,197,94,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <CheckCircle2 size={16} color="var(--color-success)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{activity.title}</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{activity.phase}</div>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                  {activity.date ? new Date(activity.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }) : 'Recently'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
