import { useQuery } from '@tanstack/react-query';
import { skillGapApi } from '../lib/api';
import { useState } from 'react';
import { Loader2, Target, TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';

interface SkillGapProps { learnerId: number; }

const PRIORITY_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  CRITICAL:    { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',    label: 'Critical Gap' },
  RECOMMENDED: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',   label: 'Recommended' },
  OPTIONAL:    { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',    label: 'Optional' },
};

function SkillBar({ skill, priority }: { skill: any; priority: string }) {
  const cfg = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.OPTIONAL;
  const pct = (skill.current_proficiency / 5) * 100;
  const targetPct = (skill.target_proficiency / 5) * 100;
  const gapPct = skill.gap_score * 100;

  return (
    <div style={{ padding: '14px 0', borderBottom: '1px solid var(--color-border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px', fontWeight: 600 }}>{skill.skill.name}</span>
          <span style={{
            fontSize: '11px', padding: '2px 8px', borderRadius: '12px',
            background: cfg.bg, color: cfg.color, fontWeight: 600,
          }}>{cfg.label}</span>
          {skill.status === 'COMPLETED' && <CheckCircle2 size={14} color="var(--color-success)" />}
        </div>
        <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', textAlign: 'right' }}>
          <span style={{ fontWeight: 700, color: cfg.color }}>{skill.current_proficiency.toFixed(1)}</span>
          <span style={{ color: 'var(--color-text-muted)' }}> / {skill.target_proficiency.toFixed(0)}</span>
        </div>
      </div>
      {/* Stacked progress bar */}
      <div style={{ position: 'relative', height: '10px', background: 'var(--color-surface-3)', borderRadius: '5px', overflow: 'hidden' }}>
        {/* Target marker */}
        <div style={{
          position: 'absolute', left: `${targetPct}%`, top: 0, bottom: 0,
          width: '2px', background: cfg.color, opacity: 0.5, zIndex: 2,
        }} />
        {/* Current fill */}
        <div style={{
          width: `${pct}%`, height: '100%', borderRadius: '5px',
          background: skill.current_proficiency >= skill.target_proficiency
            ? 'var(--gradient-primary)'
            : `linear-gradient(90deg, ${cfg.color}aa, ${cfg.color})`,
          transition: 'width 1s ease',
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Gap: {gapPct.toFixed(0)}%
        </span>
        {skill.skill.prerequisites?.length > 0 && (
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
            Prereqs: {skill.skill.prerequisites.slice(0, 2).join(', ')}
          </span>
        )}
      </div>
    </div>
  );
}

export default function SkillGap({ learnerId }: SkillGapProps) {
  const [activeTab, setActiveTab] = useState<'all' | 'critical' | 'graph'>('all');

  const { data, isLoading } = useQuery({
    queryKey: ['skill-gaps', learnerId],
    queryFn: () => skillGapApi.get(learnerId).then(r => r.data),
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
        <Loader2 size={32} color="var(--color-primary)" style={{ animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
      </div>
    );
  }

  if (!data) return null;

  const all = [
    ...data.critical_gaps,
    ...data.recommended_gaps,
    ...data.optional_gaps,
    ...data.strong_skills,
  ];

  const radarData = all.slice(0, 8).map((s: any) => ({
    skill: s.skill.name.length > 10 ? s.skill.name.substring(0, 10) : s.skill.name,
    current: s.current_proficiency,
    target: s.target_proficiency,
  }));

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Skill Gap Analysis</h1>
          <p className="page-subtitle">
            Goal: <strong style={{ color: 'var(--color-primary-light)' }}>{data.goal}</strong>
          </p>
        </div>
        <div style={{
          padding: '12px 20px',
          background: `rgba(${data.overall_readiness > 0.6 ? '34,197,94' : '245,158,11'}, 0.1)`,
          border: `1px solid rgba(${data.overall_readiness > 0.6 ? '34,197,94' : '245,158,11'}, 0.3)`,
          borderRadius: 'var(--radius-lg)',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 900, color: data.overall_readiness > 0.6 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {(data.overall_readiness * 100).toFixed(0)}%
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Overall Readiness</div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { icon: <CheckCircle2 size={20} color="var(--color-success)" />, bg: 'rgba(34,197,94,0.1)', value: data.strong_skills?.length, label: 'Strong Skills' },
          { icon: <AlertCircle size={20} color="var(--color-danger)" />, bg: 'rgba(239,68,68,0.1)', value: data.critical_gaps?.length, label: 'Critical Gaps' },
          { icon: <Target size={20} color="var(--color-warning)" />, bg: 'rgba(245,158,11,0.1)', value: data.recommended_gaps?.length, label: 'Recommended Gaps' },
          { icon: <TrendingUp size={20} color="var(--color-primary-light)" />, bg: 'rgba(99,102,241,0.1)', value: data.optional_gaps?.length, label: 'Optional Skills' },
        ].map((s, i) => (
          <div key={i} className="stat-card">
            <div className="stat-icon" style={{ background: s.bg }}>{s.icon}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '1.5rem', background: 'var(--color-surface-2)', padding: '4px', borderRadius: '10px', width: 'fit-content' }}>
        {[{ key: 'all', label: 'All Skills' }, { key: 'critical', label: `Critical (${data.critical_gaps?.length})` }, { key: 'graph', label: 'Radar Chart' }].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
              background: activeTab === tab.key ? 'var(--gradient-primary)' : 'transparent',
              color: activeTab === tab.key ? 'white' : 'var(--color-text-secondary)',
              fontSize: '13px', fontWeight: 600, transition: 'all 0.2s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'graph' ? (
        <div className="card">
          <h3 style={{ marginBottom: '1.5rem', fontSize: '15px', fontWeight: 700 }}>Skill Radar — Current vs Target</h3>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="var(--color-border)" />
              <PolarAngleAxis dataKey="skill" tick={{ fontSize: 12, fill: 'var(--color-text-secondary)' }} />
              <Radar name="Current" dataKey="current" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
              <Radar name="Target" dataKey="target" stroke="#14b8a6" fill="#14b8a6" fillOpacity={0.1} strokeDasharray="4 2" />
              <Tooltip contentStyle={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)', borderRadius: '8px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          {/* Critical */}
          {(activeTab === 'all' || activeTab === 'critical') && data.critical_gaps?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-danger)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} /> Critical Gaps
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                These must be addressed to achieve your goal
              </p>
              {data.critical_gaps.map((s: any) => (
                <SkillBar key={s.id} skill={s} priority="CRITICAL" />
              ))}
            </div>
          )}

          {/* Recommended */}
          {activeTab === 'all' && data.recommended_gaps?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-warning)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={16} /> Recommended Skills
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                Important for professional-level proficiency
              </p>
              {data.recommended_gaps.map((s: any) => (
                <SkillBar key={s.id} skill={s} priority="RECOMMENDED" />
              ))}
            </div>
          )}

          {/* Strong skills */}
          {activeTab === 'all' && data.strong_skills?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-success)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={16} /> Strong Skills
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                You've already mastered these
              </p>
              {data.strong_skills.map((s: any) => (
                <SkillBar key={s.id} skill={s} priority="OPTIONAL" />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Analysis summary */}
      <div className="insight-card" style={{ marginTop: '1.5rem' }}>
        <div style={{ fontSize: '24px' }}>🤖</div>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-primary-light)', marginBottom: '4px' }}>AI Analysis Summary</div>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>{data.analysis_summary}</p>
        </div>
      </div>
    </div>
  );
}
