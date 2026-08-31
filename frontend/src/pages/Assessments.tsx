import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assessmentApi, catalogApi, skillGapApi } from '../lib/api';
import { useState } from 'react';
import { Loader2, Star, CheckCircle2, ChevronRight, BookOpen, RefreshCw } from 'lucide-react';

interface AssessmentsProps { learnerId: number; }

function AssessmentResult({ assessment }: { assessment: any }) {
  const score = assessment.score_percentage || 0;
  const color = score >= 80 ? 'var(--color-success)' : score >= 60 ? 'var(--color-warning)' : 'var(--color-danger)';

  return (
    <div className="card card-hover" style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 700 }}>{assessment.title || assessment.skill?.name}</h3>
          <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            {assessment.skill?.name} · {assessment.total_questions} questions
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '2rem', fontWeight: 900, color }}>{score.toFixed(0)}%</div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
            {assessment.correct_answers}/{assessment.total_questions} correct
          </div>
        </div>
      </div>
      <div style={{ height: '8px', background: 'var(--color-surface-3)', borderRadius: '4px', overflow: 'hidden' }}>
        <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: '4px', transition: 'width 1s ease' }} />
      </div>
      {assessment.estimated_proficiency > 0 && (
        <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Estimated proficiency: <strong>{assessment.estimated_proficiency.toFixed(1)} / 5</strong>
        </div>
      )}
    </div>
  );
}

function ActiveAssessment({ assessment, onSubmit }: { assessment: any; onSubmit: (answers: Record<number, string>) => void }) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<any>(null);

  const submitMutation = useMutation({
    mutationFn: (ans: Record<number, string>) => assessmentApi.submit(assessment.id, ans),
    onSuccess: (res) => {
      setSubmitted(true);
      setResult(res.data);
      onSubmit({});
    },
  });

  const OPTIONS = ['A', 'B', 'C', 'D'];

  if (submitted && result) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>
            {result.score_percentage >= 80 ? '🎉' : result.score_percentage >= 60 ? '👍' : '📚'}
          </div>
          <h2 style={{ fontSize: '2rem', fontWeight: 900, color: result.score_percentage >= 80 ? 'var(--color-success)' : 'var(--color-warning)', marginBottom: '8px' }}>
            {result.score_percentage.toFixed(0)}%
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>
            {result.correct_answers} / {result.total_questions} correct
          </p>
          <div style={{
            padding: '12px 20px',
            background: 'rgba(99,102,241,0.08)',
            border: '1px solid rgba(99,102,241,0.2)',
            borderRadius: 'var(--radius-md)',
            fontSize: '14px',
            color: 'var(--color-text-secondary)',
            lineHeight: 1.6,
          }}>
            {result.adaptation_message}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.5rem' }}>{assessment.title}</h2>
      <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '1.5rem' }}>
        {assessment.description} · Answer all {assessment.total_questions} questions
      </p>

      {assessment.questions?.map((q: any, qi: number) => (
        <div key={q.id} className="question-card">
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <span style={{
              width: 24, height: 24, borderRadius: '50%',
              background: 'var(--gradient-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '12px', fontWeight: 700, color: 'white', flexShrink: 0,
            }}>{qi + 1}</span>
            <p style={{ fontSize: '14px', fontWeight: 600, lineHeight: 1.5 }}>{q.question_text}</p>
          </div>
          <div>
            {(q.options || []).map((opt: string, oi: number) => (
              <button
                key={oi}
                className={`option-btn ${answers[q.id] === OPTIONS[oi] ? 'selected' : ''}`}
                onClick={() => setAnswers(prev => ({ ...prev, [q.id]: OPTIONS[oi] }))}
              >
                <strong style={{ color: 'var(--color-primary-light)', marginRight: '8px' }}>{OPTIONS[oi]}.</strong>
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}

      <button
        className="btn btn-primary"
        onClick={() => submitMutation.mutate(answers)}
        disabled={Object.keys(answers).length < (assessment.questions?.length || 0) || submitMutation.isPending}
        style={{ width: '100%', justifyContent: 'center' }}
      >
        {submitMutation.isPending ? <Loader2 size={16} /> : <CheckCircle2 size={16} />}
        Submit Assessment ({Object.keys(answers).length}/{assessment.questions?.length || 0} answered)
      </button>
    </div>
  );
}

export default function Assessments({ learnerId }: AssessmentsProps) {
  const [activeAssessment, setActiveAssessment] = useState<any>(null);
  const qc = useQueryClient();

  const { data: history = [], isLoading: histLoading } = useQuery({
    queryKey: ['assessments', learnerId],
    queryFn: () => assessmentApi.getByLearner(learnerId).then(r => r.data),
  });

  const { data: skillGaps, isLoading: gapsLoading } = useQuery({
    queryKey: ['skill-gaps', learnerId],
    queryFn: () => skillGapApi.get(learnerId).then(r => r.data),
  });

  const { data: allSkills = [], isLoading: skillsLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: () => catalogApi.getSkills().then(r => r.data),
  });

  const generateMutation = useMutation({
    mutationFn: ({ skillId }: { skillId: number }) =>
      assessmentApi.generate(learnerId, skillId, 5),
    onSuccess: (res) => {
      setActiveAssessment(res.data);
      qc.invalidateQueries({ queryKey: ['assessments', learnerId] });
    },
  });

  // Extract learner's custom skills from their gap analysis
  const learnerSkillsMap = new Map<number, any>();
  if (skillGaps) {
    [
      ...(skillGaps.critical_gaps || []),
      ...(skillGaps.recommended_gaps || []),
      ...(skillGaps.optional_gaps || []),
      ...(skillGaps.strong_skills || []),
    ].forEach((g: any) => {
      if (g.skill?.id) {
        learnerSkillsMap.set(g.skill.id, {
          ...g.skill,
          priority: g.priority,
          current_proficiency: g.current_proficiency,
          target_proficiency: g.target_proficiency,
        });
      }
    });
  }

  const targetedSkills = learnerSkillsMap.size > 0 
    ? Array.from(learnerSkillsMap.values())
    : allSkills.slice(0, 8);

  if (activeAssessment) {
    return (
      <div className="fade-in">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1.5rem' }}>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setActiveAssessment(null)}
          >
            ← Back
          </button>
          <h1 className="page-title">Assessment</h1>
        </div>
        <ActiveAssessment
          assessment={activeAssessment}
          onSubmit={() => {
            qc.invalidateQueries({ queryKey: ['assessments', learnerId] });
            setTimeout(() => setActiveAssessment(null), 3000);
          }}
        />
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Skill Assessments</h1>
          <p className="page-subtitle">Test your knowledge — results adapt your learning path</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Take an assessment */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '0.5rem' }}>Take an Assessment</h3>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '1.5rem' }}>
            5-question quizzes that measure your real skill level and update your roadmap
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {gapsLoading || skillsLoading ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <Loader2 size={24} color="var(--color-primary)" style={{ animation: 'spin 1s linear infinite' }} />
                <style>{`@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}`}</style>
              </div>
            ) : targetedSkills.map((skill: any) => {
              const completed = history.find((a: any) => a.skill?.id === skill.id && a.status === 'COMPLETED');
              return (
                <div key={skill.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '12px 14px',
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <BookOpen size={16} color="var(--color-primary-light)" />
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600 }}>{skill.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                        {skill.domain} · Difficulty {skill.difficulty_level}/5
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {completed && (
                      <span style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: 600 }}>
                        {completed.score_percentage?.toFixed(0)}% ✓
                      </span>
                    )}
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => generateMutation.mutate({ skillId: skill.id })}
                      disabled={generateMutation.isPending}
                    >
                      {generateMutation.isPending ? <Loader2 size={12} /> : completed ? <RefreshCw size={12} /> : <ChevronRight size={12} />}
                      {completed ? 'Retry' : 'Start'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Past results */}
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '1rem' }}>Past Results</h3>
          {histLoading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <Loader2 size={24} color="var(--color-primary)" style={{ animation: 'spin 1s linear infinite' }} />
            </div>
          ) : history.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: '3rem',
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
              color: 'var(--color-text-muted)',
            }}>
              <Star size={32} style={{ marginBottom: '12px', opacity: 0.4 }} />
              <div>No assessments completed yet</div>
              <div style={{ fontSize: '12px', marginTop: '4px' }}>
                Take your first assessment to measure your skill level
              </div>
            </div>
          ) : (
            history.map((a: any) => <AssessmentResult key={a.id} assessment={a} />)
          )}
        </div>
      </div>
    </div>
  );
}
