import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { Newspaper, Sparkles, Clock, Globe, BarChart2, ShieldAlert } from 'lucide-react';

export const AINewspaper: React.FC = () => {
  const [edition, setEdition] = useState<'PRE_MARKET' | 'INTRADAY' | 'CLOSING'>('INTRADAY');
  const [newspaper, setNewspaper] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    ApiClient.getAINewspaper(edition)
      .then(setNewspaper)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [edition]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      {/* Newspaper Masthead */}
      <div className="card" style={{
        textAlign: 'center',
        padding: '2rem 1.5rem',
        background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-md)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--accent-purple)', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '8px' }}>
          <Sparkles size={16} />
          <span>The Dalal Street Intelligence Syndicate</span>
        </div>

        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.03em', color: '#fff', textTransform: 'uppercase', borderBottom: '2px solid rgba(255,255,255,0.1)', paddingBottom: '12px', marginBottom: '12px' }}>
          AI MARKET CHRONICLE
        </h1>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Edition: <b>{edition.replace('_', ' ')}</b></span>
          <span>Date: <b>{new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</b></span>
          <span>Exchange: <b>NSE / BSE India</b></span>
        </div>
      </div>

      {/* Edition Switcher */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
        {[
          { key: 'PRE_MARKET', label: '🌅 Pre-Market Briefing' },
          { key: 'INTRADAY', label: '⚡ Intraday Pulse' },
          { key: 'CLOSING', label: '📊 Closing Bell Wrap' }
        ].map((item) => (
          <button
            key={item.key}
            onClick={() => setEdition(item.key as any)}
            className={`btn ${edition === item.key ? 'btn-purple' : 'btn-secondary'}`}
            style={{ padding: '8px 20px', borderRadius: '10px', fontSize: '0.85rem' }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Main Articles */}
      {newspaper?.articles && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {newspaper.articles.map((art: any, idx: number) => (
            <div key={idx} className="card" style={{ padding: '1.5rem', borderLeft: '4px solid var(--accent-purple)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span className="badge badge-purple">{art.section}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Verified Synthesized Feed</span>
              </div>

              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
                {art.headline}
              </h3>

              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '16px' }}>
                {art.content}
              </p>

              {art.data_points && art.data_points.length > 0 && (
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  {art.data_points.map((dp: string, i: number) => (
                    <div key={i} style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '6px 12px', fontSize: '0.75rem', color: '#fff', fontWeight: 500 }} className="mono">
                      • {dp}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Editorial Disclaimer */}
      <div style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)', padding: '1rem' }}>
        {newspaper?.disclaimer || 'AI Market Newspaper compiles authorized market feeds deterministically. Not investment advice.'}
      </div>
    </div>
  );
};
