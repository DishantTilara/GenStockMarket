import React, { useState, useRef, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { Sparkles, Send, Bot, User as UserIcon, Terminal, CheckCircle2, Zap } from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: any[];
  timestamp: string;
}

export const AIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Welcome to the **Indian Stock Market GenAI Intelligence Suite**.\n\nI am grounded in real-time NSE order books, deterministic technical indicators, company fundamentals, and corporate filings. You can ask me:\n- *"Analyze RELIANCE with current technical levels"*\n- *"What are TCS valuations and quarterly commentary?"*\n- *"Is NIFTY 50 in a bullish or bearish regime today?"*\n- *"Scan for unusual volume breakouts"*\n\nAll answers strictly execute backend tools with verified live market parameters.`,
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const query = customQuery || input;
    if (!query.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(2, 9),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customQuery) setInput('');
    setIsLoading(true);

    try {
      const resp = await ApiClient.sendAIChat(query, conversationId);
      setConversationId(resp.conversation_id);

      const aiMsg: ChatMessage = {
        id: Math.random().toString(36).substring(2, 9),
        role: 'assistant',
        content: resp.reply,
        toolCalls: resp.tool_calls_executed,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: Math.random().toString(36).substring(2, 9),
        role: 'assistant',
        content: `Error contacting GenAI Engine: ${err.message || 'Please check backend connectivity.'}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', gap: '1rem' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #a855f7 0%, #38bdf8 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(168, 85, 247, 0.4)'
          }}>
            <Sparkles size={20} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800 }}>Dalal Street GenAI Analyst</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Deterministic Tool-Grounded Intelligence • Multi-Provider Model Abstraction
            </p>
          </div>
        </div>

        {/* Quick query chips */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {['Analyze RELIANCE', 'Analyze TCS', 'NSE Market Regime', 'Find Volume Breakouts'].map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleSend(undefined, prompt)}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '6px 12px', borderRadius: '8px' }}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="card" style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.id}
              style={{
                display: 'flex',
                gap: '12px',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: isUser ? '75%' : '85%'
              }}
            >
              {!isUser && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'var(--accent-purple-bg)',
                  border: '1px solid var(--accent-purple)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <Bot size={18} color="var(--accent-purple)" />
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
                <div style={{
                  padding: '1rem 1.25rem',
                  borderRadius: '12px',
                  background: isUser ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'rgba(30, 41, 59, 0.6)',
                  border: isUser ? 'none' : '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                  boxShadow: var(--shadow-sm),
                  whiteSpace: 'pre-wrap'
                }}>
                  {m.content}
                </div>

                {/* Show executed tool calls badge if any */}
                {m.toolCalls && m.toolCalls.length > 0 && (
                  <div style={{
                    background: 'rgba(15, 23, 42, 0.7)',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-purple)', fontWeight: 600, marginBottom: '4px' }}>
                      <Terminal size={14} />
                      <span>Verified Tool Execution Disclosure ({m.toolCalls.length})</span>
                    </div>
                    {m.toolCalls.map((tc: any, idx: number) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem' }}>
                        <CheckCircle2 size={12} color="var(--accent-green)" />
                        <span className="mono" style={{ color: '#fff' }}>{tc.name}</span>
                        <span>({JSON.stringify(tc.arguments)})</span>
                      </div>
                    ))}
                  </div>
                )}

                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', alignSelf: isUser ? 'flex-end' : 'flex-start' }}>
                  {m.timestamp}
                </span>
              </div>

              {isUser && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'var(--bg-tertiary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <UserIcon size={18} color="var(--text-secondary)" />
                </div>
              )}
            </div>
          );
        })}
        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-purple)', fontSize: '0.85rem' }}>
            <Sparkles className="animate-spin" size={18} />
            <span>Consulting deterministic market tools & synthesizing intelligence...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          placeholder="Ask anything about Indian stocks, indicators, or sector trends..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
          className="input"
          style={{ padding: '0.85rem 1.25rem', fontSize: '0.95rem' }}
        />
        <button type="submit" disabled={isLoading || !input.trim()} className="btn btn-purple" style={{ padding: '0 24px' }}>
          <Send size={18} />
          <span>Ask AI</span>
        </button>
      </form>
    </div>
  );
};
