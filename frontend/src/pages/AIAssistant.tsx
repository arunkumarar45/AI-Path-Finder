import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assistantApi } from '../lib/api';
import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, User, Trash2, Sparkles } from 'lucide-react';

interface AIAssistantProps { learnerId: number; }

const QUICK_PROMPTS = [
  "What should I learn next?",
  "Why is Spring Boot recommended for me?",
  "Am I on track for my 4-month goal?",
  "Can I skip REST APIs if I already know them?",
  "What's my biggest skill gap right now?",
  "How many hours should I study this week?",
];

function formatMessage(text: string) {
  // Bold **text**
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

export default function AIAssistant({ learnerId }: AIAssistantProps) {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const qc = useQueryClient();

  const { data: history = [], isLoading } = useQuery({
    queryKey: ['chat', learnerId],
    queryFn: () => assistantApi.getHistory(learnerId).then(r => r.data),
  });

  const sendMutation = useMutation({
    mutationFn: (msg: string) => assistantApi.chat(learnerId, msg),
    onMutate: () => setIsTyping(true),
    onSettled: () => setIsTyping(false),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chat', learnerId] });
    },
  });

  const clearMutation = useMutation({
    mutationFn: () => assistantApi.clearHistory(learnerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chat', learnerId] }),
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, isTyping]);

  const handleSend = async () => {
    const msg = message.trim();
    if (!msg || sendMutation.isPending) return;
    setMessage('');
    await sendMutation.mutateAsync(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fade-in" style={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <div className="page-header" style={{ marginBottom: '1rem' }}>
        <div>
          <h1 className="page-title">AI Learning Mentor</h1>
          <p className="page-subtitle">
            Ask me anything about your learning path — I know your profile, skills, and roadmap
          </p>
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => clearMutation.mutate()}
          disabled={clearMutation.isPending}
        >
          <Trash2 size={14} /> Clear Chat
        </button>
      </div>

      <div className="chat-container" style={{ flex: 1, minHeight: 0 }}>
        {/* Messages */}
        <div className="chat-messages">
          {/* Welcome message if empty */}
          {!isLoading && history.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{
                width: 64, height: 64, borderRadius: '50%',
                background: 'var(--gradient-secondary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 1rem', fontSize: '32px',
              }}>🤖</div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '8px' }}>
                Hi! I'm your AI Learning Mentor
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', maxWidth: '400px', margin: '0 auto' }}>
                I know your current skills, learning goals, and roadmap. Ask me anything — from what to study next to why a topic was recommended.
              </p>
            </div>
          )}

          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
              <Loader2 size={24} color="var(--color-primary)" style={{ animation: 'spin 1s linear infinite' }} />
              <style>{`@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}`}</style>
            </div>
          )}

          {history.map((msg: any) => (
            <div key={msg.id} className={`chat-message ${msg.role === 'USER' ? 'user' : 'assistant'}`}>
              <div className={`chat-avatar ${msg.role === 'USER' ? 'user-avatar' : 'ai-avatar'}`}>
                {msg.role === 'USER' ? <User size={18} /> : '🤖'}
              </div>
              <div className={`chat-bubble ${msg.role === 'USER' ? 'user-bubble' : 'ai-bubble'}`}>
                <div dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
                <div style={{ fontSize: '11px', opacity: 0.6, marginTop: '4px', textAlign: msg.role === 'USER' ? 'right' : 'left' }}>
                  {new Date(msg.timestamp).toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="chat-message assistant">
              <div className="chat-avatar ai-avatar">🤖</div>
              <div className="chat-bubble ai-bubble">
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                  <span style={{ width: 8, height: 8, background: 'var(--color-primary)', borderRadius: '50%', animation: 'dot 1.2s 0s infinite' }} />
                  <span style={{ width: 8, height: 8, background: 'var(--color-primary)', borderRadius: '50%', animation: 'dot 1.2s 0.2s infinite' }} />
                  <span style={{ width: 8, height: 8, background: 'var(--color-primary)', borderRadius: '50%', animation: 'dot 1.2s 0.4s infinite' }} />
                </div>
                <style>{`@keyframes dot{0%,80%,100%{opacity:.3}40%{opacity:1}}`}</style>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick prompts */}
        {history.length < 2 && (
          <div style={{ padding: '0 1rem 0.75rem', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {QUICK_PROMPTS.map(prompt => (
              <button
                key={prompt}
                onClick={() => { setMessage(prompt); inputRef.current?.focus(); }}
                style={{
                  padding: '6px 12px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '20px',
                  background: 'var(--color-surface-2)',
                  color: 'var(--color-text-secondary)',
                  fontSize: '12px',
                  cursor: 'pointer',
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
                {prompt}
              </button>
            ))}
          </div>
        )}

        {/* Input area */}
        <div className="chat-input-container">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Ask your AI mentor anything about your learning path..."
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            style={{ height: 'auto' }}
          />
          <button
            className="btn btn-primary"
            onClick={handleSend}
            disabled={sendMutation.isPending || !message.trim()}
            style={{ padding: '10px 16px' }}
          >
            {sendMutation.isPending ? <Loader2 size={18} /> : <Send size={18} />}
          </button>
        </div>
      </div>

      {/* AI capability note */}
      <div style={{
        marginTop: '8px',
        display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center',
      }}>
        <Sparkles size={12} color="var(--color-secondary)" />
        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Powered by Gemini AI · Grounded in your actual learning data · Works offline with deterministic fallback
        </span>
      </div>
    </div>
  );
}
