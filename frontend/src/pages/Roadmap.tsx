import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { roadmapApi, feedbackApi } from '../lib/api';
import { useState } from 'react';
import {
  ChevronDown, CheckCircle2, Clock, Loader2, Play,
  ThumbsUp, Zap, BookOpen, Wrench, ExternalLink,
  Trophy, Star, ChevronUp, X
} from 'lucide-react';

interface RoadmapProps {
  learnerId: number;
}

const STATUS_CONFIG: Record<string, { icon: string; className: string; label: string }> = {
  COMPLETED: { icon: '✓', className: 'status-completed', label: 'Completed' },
  IN_PROGRESS: { icon: '▶', className: 'status-in-progress', label: 'In Progress' },
  NOT_STARTED: { icon: '○', className: 'status-not-started', label: 'Not Started' },
  SKIPPED: { icon: '—', className: 'status-skipped', label: 'Skipped' },
};

const TYPE_ICONS: Record<string, any> = {
  LEARN: BookOpen,
  PROJECT: Wrench,
  ASSESSMENT: Star,
  PRACTICE: Zap,
};

function FeedbackPanel({ itemId, learnerId, onClose }: { itemId: number; learnerId: number; onClose: () => void }) {
  const qc = useQueryClient();
  const [sent, setSent] = useState(false);

  const mutation = useMutation({
    mutationFn: (type: string) => feedbackApi.submit({
      learner_id: learnerId,
      roadmap_item_id: itemId,
      type,
    }),
    onSuccess: () => {
      setSent(true);
      qc.invalidateQueries({ queryKey: ['roadmap', learnerId] });
      setTimeout(onClose, 1500);
    },
  });

  if (sent) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--color-success)' }}>
        ✅ Feedback received! Your roadmap will adapt.
      </div>
    );
  }

  const FEEDBACK_OPTIONS = [
    { type: 'TOO_EASY', label: '😌 Too easy', desc: 'I already know this' },
    { type: 'TOO_DIFFICULT', label: '😰 Too difficult', desc: 'Need prerequisites first' },
    { type: 'ALREADY_KNOW', label: '✅ Already know this', desc: 'Skip and update my profile' },
    { type: 'VERY_USEFUL', label: '⭐ Very useful!', desc: 'Prioritize similar content' },
    { type: 'SKIP', label: '⏭️ Skip this item', desc: 'Move to next item' },
    { type: 'NEED_MORE_PRACTICE', label: '🔄 Need more practice', desc: 'Add extra exercises' },
  ];

  return (
    <div style={{ padding: '1rem', borderTop: '1px solid var(--color-border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          📝 Give feedback (adapts your roadmap)
        </span>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}>
          <X size={16} />
        </button>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {FEEDBACK_OPTIONS.map(opt => (
          <button
            key={opt.type}
            className="feedback-chip"
            onClick={() => mutation.mutate(opt.type)}
            disabled={mutation.isPending}
            title={opt.desc}
          >
            {mutation.isPending ? <Loader2 size={12} /> : null}
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

interface RoadmapItemCardProps {
  item: any;
  learnerId: number;
}

function RoadmapItemCard({ item, learnerId }: RoadmapItemCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const qc = useQueryClient();

  const statusCfg = STATUS_CONFIG[item.status] || STATUS_CONFIG.NOT_STARTED;
  const TypeIcon = TYPE_ICONS[item.type] || BookOpen;

  const statusMutation = useMutation({
    mutationFn: (status: string) => roadmapApi.updateItemStatus(item.id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roadmap', learnerId] }),
  });

        const isActive = item.status === 'IN_PROGRESS' || item.status === 'NOT_STARTED';
        void isActive;

  return (
    <div style={{ borderTop: '1px solid var(--color-border)' }}>
      {/* Main row */}
      <div
        className="roadmap-item"
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: 'pointer' }}
      >
        {/* Status indicator */}
        <div className={`roadmap-item-status ${statusCfg.className}`}>
          {statusCfg.icon}
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text)' }}>
              {item.title}
            </span>
            {item.is_milestone && (
              <span style={{ fontSize: '12px', color: 'var(--color-warning)' }}>🏆 Milestone</span>
            )}
            <span className="badge badge-in-progress" style={{ fontSize: '10px' }}>
              <TypeIcon size={10} /> {item.type}
            </span>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={12} /> {item.estimated_hours}h
            </span>
            {item.skills_gained && (
              <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                🎯 {Array.isArray(item.skills_gained) ? item.skills_gained.slice(0, 2).join(', ') : item.skills_gained}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }} onClick={e => e.stopPropagation()}>
          {item.resource?.url && (
            <a href={item.resource.url} target="_blank" rel="noopener" className="btn btn-ghost btn-sm" title="Open resource">
              <ExternalLink size={14} />
            </a>
          )}
          {item.status === 'NOT_STARTED' && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => statusMutation.mutate('IN_PROGRESS')}
              disabled={statusMutation.isPending}
            >
              <Play size={12} /> Start
            </button>
          )}
          {item.status === 'IN_PROGRESS' && (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => statusMutation.mutate('COMPLETED')}
              disabled={statusMutation.isPending}
            >
              {statusMutation.isPending ? <Loader2 size={12} /> : <CheckCircle2 size={12} />}
              Done
            </button>
          )}
          {item.status === 'COMPLETED' && (
            <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>✅ Done</span>
          )}
          {expanded ? <ChevronUp size={16} color="var(--color-text-muted)" /> : <ChevronDown size={16} color="var(--color-text-muted)" />}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem 1.5rem' }}>
          {/* Description */}
          {item.description && (
            <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '1rem', lineHeight: 1.6 }}>
              {item.description}
            </p>
          )}

          {/* Why recommended */}
          {item.why_recommended && (
            <div className="insight-card" style={{ marginBottom: '1rem' }}>
              <Zap size={14} color="var(--color-primary-light)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-primary-light)', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Why Recommended
                </div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                  {item.why_recommended}
                </div>
              </div>
            </div>
          )}

          {/* Resource */}
          {item.resource && (
            <div style={{
              padding: '10px 14px',
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '1rem',
            }}>
              <BookOpen size={16} color="var(--color-text-muted)" style={{ flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{item.resource.title}</div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                  {item.resource.provider} · {item.resource.estimated_hours}h
                  {item.resource.is_free && ' · 🆓 Free'}
                  {item.resource.rating && ` · ⭐ ${item.resource.rating}`}
                </div>
              </div>
              {item.resource.url && (
                <a href={item.resource.url} target="_blank" rel="noopener" className="btn btn-secondary btn-sm">
                  Open <ExternalLink size={12} />
                </a>
              )}
            </div>
          )}

          {/* Project details */}
          {item.project_info && (
            <div style={{
              padding: '12px 14px',
              background: 'rgba(245,158,11,0.05)',
              border: '1px solid rgba(245,158,11,0.2)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1rem',
            }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-warning)', marginBottom: '8px', textTransform: 'uppercase' }}>
                🛠️ Project Details
              </div>
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                {item.project_info.objective}
              </div>
              {item.project_info.requirements && (
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  {item.project_info.requirements.map((r: string, i: number) => (
                    <li key={i} style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '2px' }}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Milestone */}
          {item.milestone_text && (
            <div style={{
              padding: '10px 14px',
              background: 'rgba(99,102,241,0.08)',
              border: '1px solid rgba(99,102,241,0.2)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1rem',
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
            }}>
              <Trophy size={16} color="var(--color-primary-light)" />
              <span style={{ fontSize: '13px', color: 'var(--color-primary-light)' }}>{item.milestone_text}</span>
            </div>
          )}

          {/* Scoring */}
          {item.scoring_metadata && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Recommendation Score: {(item.scoring_metadata.total_score * 100).toFixed(0)}%
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {Object.entries(item.scoring_metadata).filter(([k]) => k !== 'total_score').map(([key, val]: any) => (
                  <span key={key} style={{
                    fontSize: '11px',
                    padding: '3px 8px',
                    background: 'var(--color-surface-3)',
                    borderRadius: '4px',
                    color: 'var(--color-text-muted)',
                  }}>
                    {key.replace(/_/g, ' ')}: <strong style={{ color: val > 0.7 ? 'var(--color-success)' : 'var(--color-text-secondary)' }}>{(val * 100).toFixed(0)}%</strong>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Feedback trigger */}
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setShowFeedback(!showFeedback)}
          >
            <ThumbsUp size={14} />
            Give Feedback
          </button>
        </div>
      )}

      {/* Feedback panel */}
      {showFeedback && (
        <FeedbackPanel itemId={item.id} learnerId={learnerId} onClose={() => setShowFeedback(false)} />
      )}
    </div>
  );
}

export default function Roadmap({ learnerId }: RoadmapProps) {
  const [openPhases, setOpenPhases] = useState<Set<number>>(new Set([1, 2]));

  const { data, isLoading, error } = useQuery({
    queryKey: ['roadmap', learnerId],
    queryFn: () => roadmapApi.get(learnerId).then(r => r.data),
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
        <Loader2 size={32} color="var(--color-primary)" style={{ animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--color-text-secondary)' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🗺️</div>
        <div style={{ marginBottom: '1rem' }}>No roadmap found. Generate one from your profile.</div>
      </div>
    );
  }

  // Group items by phase
  const phases: Record<number, { name: string; items: any[] }> = {};
  for (const item of data.items || []) {
    if (!phases[item.phase_number]) {
      phases[item.phase_number] = { name: item.phase_name || `Phase ${item.phase_number}`, items: [] };
    }
    phases[item.phase_number].items.push(item);
  }

  const togglePhase = (phaseNum: number) => {
    const next = new Set(openPhases);
    if (next.has(phaseNum)) next.delete(phaseNum);
    else next.add(phaseNum);
    setOpenPhases(next);
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Learning Roadmap</h1>
          <p className="page-subtitle">{data.title}</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '24px', fontWeight: 800, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              {data.completion_percentage?.toFixed(0)}%
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
              {data.completed_items} / {data.total_items} complete
            </div>
          </div>
        </div>
      </div>

      {/* Roadmap summary */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem',
      }}>
        {[
          { label: 'Total Phases', value: data.total_phases },
          { label: 'Total Items', value: data.total_items },
          { label: 'Est. Completion', value: data.estimated_completion_date },
          { label: 'Schedule', value: data.schedule_status?.replace(/_/g, ' ') || 'On Track' },
        ].map((s, i) => (
          <div key={i} className="card" style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-primary-light)' }}>{s.value}</div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Overall progress bar */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Overall Progress</span>
          <span style={{ fontSize: '13px', color: 'var(--color-primary-light)' }}>{data.completion_percentage?.toFixed(1)}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${data.completion_percentage || 0}%` }} />
        </div>
        {data.ai_reasoning && (
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '10px', lineHeight: 1.5 }}>
            💡 {data.ai_reasoning}
          </p>
        )}
      </div>

      {/* Phase cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {Object.entries(phases).map(([phaseNum, phase]) => {
          const pn = parseInt(phaseNum);
          const isOpen = openPhases.has(pn);
          const phaseItems = phase.items;
          const completedCount = phaseItems.filter((i: any) => i.status === 'COMPLETED' || i.status === 'SKIPPED').length;
          const isCurrentPhase = data.current_phase === pn;
          const phaseProgress = phaseItems.length > 0 ? (completedCount / phaseItems.length) * 100 : 0;

          return (
            <div key={pn} className={`phase-card ${isCurrentPhase ? 'active' : ''}`}>
              <div className="phase-header" onClick={() => togglePhase(pn)}>
                {/* Phase number */}
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: phaseProgress === 100 ? 'var(--gradient-primary)' : isCurrentPhase ? 'rgba(99,102,241,0.2)' : 'var(--color-surface-3)',
                  border: `2px solid ${phaseProgress === 100 ? 'transparent' : isCurrentPhase ? 'var(--color-primary)' : 'var(--color-border)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '14px', fontWeight: 700, flexShrink: 0,
                  color: phaseProgress === 100 ? 'white' : isCurrentPhase ? 'var(--color-primary-light)' : 'var(--color-text-muted)',
                }}>
                  {phaseProgress === 100 ? '✓' : pn}
                </div>

                {/* Phase info */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '15px', fontWeight: 700 }}>{phase.name}</span>
                    {isCurrentPhase && (
                      <span className="badge badge-in-progress">Current</span>
                    )}
                    {phaseProgress === 100 && (
                      <span className="badge badge-completed">✓ Complete</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '100px', height: '4px', background: 'var(--color-surface-3)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${phaseProgress}%`, height: '100%', background: 'var(--gradient-primary)', borderRadius: '2px' }} />
                    </div>
                    <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                      {completedCount}/{phaseItems.length} items
                    </span>
                  </div>
                </div>

                {isOpen ? <ChevronUp size={18} color="var(--color-text-muted)" /> : <ChevronDown size={18} color="var(--color-text-muted)" />}
              </div>

              {isOpen && (
                <div className="phase-body">
                  {phaseItems.map((item: any) => (
                    <RoadmapItemCard key={item.id} item={item} learnerId={learnerId} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
