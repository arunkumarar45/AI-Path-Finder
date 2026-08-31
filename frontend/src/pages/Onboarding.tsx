import { useState } from 'react';
import { Sparkles, ArrowRight, User, Loader2 } from 'lucide-react';
import { learnerApi, skillGapApi, roadmapApi } from '../lib/api';

interface OnboardingProps {
  onComplete: (learnerId: number) => void;
}

const DEMO_GOALS = [
  "I want to become a Backend Java Developer in 4 months. I know Core Java, OOP, and SQL. I can study 8 hours per week.",
  "I want to be a fullstack developer. I know HTML and some JavaScript. Available 10 hours/week.",
  "I'm aiming to become a Data Scientist. I know Python basics and some statistics. 6 hours/week.",
  "I want to transition to DevOps engineering. I know Linux basics and Python. 12 hours/week.",
];

export default function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState<'welcome' | 'goal' | 'loading'>('welcome');
  const [loadingMsg, setLoadingMsg] = useState('Setting up your personalized learning path...');
  const [goal, setGoal] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const handleDemoUser = async () => {
    setStep('loading');
    setLoadingMsg('Loading demo profile...');
    try {
      const res = await learnerApi.getDemo();
      onComplete(res.data.id);
    } catch {
      setError('Failed to load demo. Please try again.');
      setStep('welcome');
    }
  };

  // After creating a learner, trigger analysis + roadmap generation
  const bootstrapNewLearner = async (learnerId: number, _goalText: string) => {
    try {
      setLoadingMsg('Analyzing your learning goals...');
      await new Promise(r => setTimeout(r, 400)); // let UI update

      setLoadingMsg('Identifying your skill gaps...');
      await skillGapApi.analyze(learnerId).catch(() => {});

      setLoadingMsg('Generating your personalized roadmap...');
      await roadmapApi.generate(learnerId, true).catch(() => {});

      setLoadingMsg('Almost done...');
      await new Promise(r => setTimeout(r, 400));
    } catch {
      // Non-fatal — user still gets to dashboard
    }
    onComplete(learnerId);
  };

  const handleSubmit = async () => {
    if (!name.trim() || !email.trim() || !goal.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setError('');
    setStep('loading');
    setLoadingMsg('Creating your account...');

    try {
      const res = await learnerApi.create({
        name,
        email,
        career_goal: goal.split('.')[0].substring(0, 200),
        goal_description: goal,
        experience_level: 'INTERMEDIATE',
        interests: [],
        completed_courses: [],
        preferred_content_types: ['COURSE', 'PROJECT', 'TUTORIAL'],
        weekly_hours_available: 8,
      });
      await bootstrapNewLearner(res.data.id, goal);
    } catch (e: any) {
      setError('Failed to create account. Please try again.');
      setStep('goal');
    }
  };

  if (step === 'loading') {
    const steps = [
      'Creating your account...',
      'Analyzing your learning goals...',
      'Identifying your skill gaps...',
      'Generating your personalized roadmap...',
      'Almost done...',
      'Loading demo profile...',
    ];
    const stepIdx = steps.indexOf(loadingMsg);
    const progressPct = stepIdx === -1 ? 20 : Math.round(((stepIdx + 1) / 5) * 100);

    return (
      <div className="onboarding-container">
        <div style={{ textAlign: 'center', maxWidth: 400 }}>
          {/* Animated logo */}
          <div style={{
            width: 72, height: 72, borderRadius: '50%',
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1.5rem',
            boxShadow: '0 0 40px rgba(99,102,241,0.4)',
            animation: 'pulse 2s infinite',
          }}>
            <Loader2 size={32} color="white" className="spin" />
          </div>

          <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-text)', marginBottom: '8px' }}>
            {loadingMsg}
          </div>

          {/* Live step messages */}
          <div style={{ color: 'var(--color-text-secondary)', marginBottom: '1.5rem', fontSize: '14px', minHeight: 20 }}>
            {loadingMsg === 'Loading demo profile...'
              ? 'Loading Alex Chen\'s profile...'
              : 'AI is building your personalized experience'}
          </div>

          {/* Progress bar */}
          <div style={{
            width: '100%', height: 6, background: 'var(--color-surface-3)',
            borderRadius: 3, overflow: 'hidden', marginBottom: '1rem',
          }}>
            <div style={{
              height: '100%', background: 'var(--gradient-primary)',
              borderRadius: 3, width: `${progressPct}%`,
              transition: 'width 0.6s ease',
            }} />
          </div>

          {/* Step labels */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, textAlign: 'left' }}>
            {['Analyze profile', 'Map skill gaps', 'Build roadmap', 'Generate insights'].map((s, i) => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                <div style={{
                  width: 16, height: 16, borderRadius: '50%', flexShrink: 0,
                  background: i < Math.floor(progressPct / 25) ? 'var(--gradient-primary)' : 'var(--color-surface-3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 10, color: 'white', transition: 'background 0.4s',
                }}>
                  {i < Math.floor(progressPct / 25) ? '✓' : ''}
                </div>
                <span style={{ color: i < Math.floor(progressPct / 25) ? 'var(--color-text)' : 'var(--color-text-muted)' }}>
                  {s}
                </span>
              </div>
            ))}
          </div>

          <style>{`.spin { animation: spin 1s linear infinite; } @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } } @keyframes pulse { 0%,100%{box-shadow:0 0 40px rgba(99,102,241,0.4)} 50%{box-shadow:0 0 60px rgba(99,102,241,0.7)} }`}</style>
        </div>
      </div>
    );
  }


  if (step === 'welcome') {
    return (
      <div className="onboarding-container">
        <div className="onboarding-card">
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <div style={{
              width: 80, height: 80, borderRadius: '20px',
              background: 'var(--gradient-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '40px', margin: '0 auto 1.5rem',
              boxShadow: '0 0 30px rgba(99,102,241,0.5)',
            }}>🧠</div>
            <h1 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: '0.5rem' }}>
              <span className="gradient-text">AI Path Finder</span>
            </h1>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '15px', lineHeight: 1.6, maxWidth: '400px', margin: '0 auto' }}>
              Personalized AI-powered learning paths built around your goals, skills, and schedule.
            </p>
          </div>

          {/* Feature pills */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center', marginBottom: '2rem' }}>
            {['🎯 Skill Gap Analysis', '🗺️ Smart Roadmaps', '🤖 AI Mentor', '📊 Progress Tracking', '✨ Adaptive Learning'].map(f => (
              <span key={f} style={{
                padding: '6px 12px',
                borderRadius: '20px',
                background: 'rgba(99,102,241,0.08)',
                border: '1px solid rgba(99,102,241,0.2)',
                fontSize: '12px',
                color: 'var(--color-primary-light)',
                fontWeight: 500,
              }}>{f}</span>
            ))}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button className="btn btn-primary btn-lg" onClick={() => setStep('goal')} style={{ justifyContent: 'center' }}>
              <User size={18} />
              Create My Learning Path
              <ArrowRight size={18} />
            </button>
            <button className="btn btn-secondary btn-lg" onClick={handleDemoUser} style={{ justifyContent: 'center' }}>
              <Sparkles size={18} />
              Try Demo (Alex Chen — Backend Java Dev)
            </button>
          </div>

          <p style={{ textAlign: 'center', fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '1.5rem' }}>
            Demo account comes pre-loaded with a realistic learning profile and 28.5% progress
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2rem' }}>
          <div style={{
            width: 44, height: 44, borderRadius: '12px',
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>🎯</div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Tell me about your goal</h2>
            <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
              I'll create a personalized roadmap just for you
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Your Name
            </label>
            <input
              className="input"
              placeholder="Alex Chen"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Email Address
            </label>
            <input
              className="input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Describe your learning goal
            </label>
            <textarea
              className="input"
              placeholder="I want to become a Backend Java Developer in 4 months. I already know Java basics and SQL. I can study 8 hours per week..."
              value={goal}
              onChange={e => setGoal(e.target.value)}
              rows={4}
            />
          </div>
        </div>

        {/* Quick fill examples */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '8px', fontWeight: 600 }}>
            Quick examples (click to use):
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {DEMO_GOALS.slice(0, 2).map((g, i) => (
              <button
                key={i}
                onClick={() => setGoal(g)}
                style={{
                  textAlign: 'left',
                  padding: '8px 12px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '8px',
                  background: 'var(--color-surface-2)',
                  color: 'var(--color-text-secondary)',
                  cursor: 'pointer',
                  fontSize: '12px',
                  lineHeight: 1.5,
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => {
                  (e.target as HTMLElement).style.borderColor = 'var(--color-primary)';
                  (e.target as HTMLElement).style.color = 'var(--color-text)';
                }}
                onMouseLeave={e => {
                  (e.target as HTMLElement).style.borderColor = 'var(--color-border)';
                  (e.target as HTMLElement).style.color = 'var(--color-text-secondary)';
                }}
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px',
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: '8px',
            color: 'var(--color-danger)',
            fontSize: '13px',
            marginBottom: '1rem',
          }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-ghost" onClick={() => setStep('welcome')}>
            Back
          </button>
          <button className="btn btn-primary" onClick={handleSubmit} style={{ flex: 1, justifyContent: 'center' }}>
            <Sparkles size={16} />
            Generate My Learning Path
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
