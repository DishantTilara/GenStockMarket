import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { Sliders, Sparkles, Play, Plus, CheckCircle2 } from 'lucide-react';

export const Strategies: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [strategies, setStrategies] = useState<any[]>([]);
  const [nlPrompt, setNlPrompt] = useState('Create a strategy where price crosses above 20 EMA and RSI is above 55 with volume 1.5x average volume');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedStrategy, setGeneratedStrategy] = useState<any>(null);

  const fetchStrategies = async () => {
    try {
      const data = await ApiClient.getStrategies();
      setStrategies(data);
    } catch {}
  };

  useEffect(() => {
    fetchStrategies();
  }, []);

  const handleGenerateStrategy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlPrompt.trim()) return;
    setIsGenerating(true);
    try {
      const res = await ApiClient.request<any>(`/strategies/nl-generate?query=${encodeURIComponent(nlPrompt)}`, { method: 'POST' });
      setGeneratedStrategy(res);
      showToast('AI synthesized strategy logic successfully', 'success');
    } catch (err: any) {
      showToast(err.message, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveStrategy = async () => {
    if (!generatedStrategy) return;
    try {
      await ApiClient.createStrategy(generatedStrategy);
      showToast('Strategy saved to library', 'success');
      setGeneratedStrategy(null);
      fetchStrategies();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Algorithmic Strategy Engine</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Design, generate via AI, and store quantitative rulesets ready for walk-forward backtesting
        </p>
      </div>

      {/* AI Strategy Generator Card */}
      <div className="card card-glow-purple">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Sparkles size={18} color="var(--accent-purple)" />
          <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>AI Natural Language Strategy Synthesizer</h4>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          Describe your quantitative entry, exit, stop loss, and target conditions in natural language.
        </p>

        <form onSubmit={handleGenerateStrategy} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={nlPrompt}
            onChange={(e) => setNlPrompt(e.target.value)}
            className="input"
            style={{ flex: 1 }}
            placeholder="e.g. Buy when 20 EMA crosses above 50 EMA and RSI is above 60 with 2% target"
          />
          <button type="submit" disabled={isGenerating} className="btn btn-purple" style={{ whiteSpace: 'nowrap' }}>
            <Sparkles size={16} />
            <span>{isGenerating ? 'Synthesizing...' : 'Generate Strategy'}</span>
          </button>
        </form>

        {/* Generated Preview */}
        {generatedStrategy && (
          <div style={{ marginTop: '1.25rem', padding: '1.25rem', background: 'rgba(15, 23, 42, 0.8)', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h5 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>{generatedStrategy.name}</h5>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={handleSaveStrategy} className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
                  Save to Library
                </button>
                <button
                  onClick={() => navigate('/backtests', { state: { strategy: generatedStrategy } })}
                  className="btn btn-purple"
                  style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                >
                  <Play size={14} />
                  <span>Run Backtest</span>
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '0.8rem' }} className="mono">
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Entry Logic:</span>
                <ul style={{ paddingLeft: '14px', color: 'var(--accent-green)', marginTop: '4px' }}>
                  {generatedStrategy.entry_rules.map((r: string, i: number) => <li key={i}>{r}</li>)}
                </ul>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Exit Logic:</span>
                <ul style={{ paddingLeft: '14px', color: 'var(--accent-red)', marginTop: '4px' }}>
                  {generatedStrategy.exit_rules.map((r: string, i: number) => <li key={i}>{r}</li>)}
                </ul>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Risk Parameters:</span>
                <div style={{ color: '#fff', marginTop: '4px' }}>Stop Loss: {generatedStrategy.stop_loss.value}%</div>
                <div style={{ color: '#fff' }}>Target: {generatedStrategy.target.value}%</div>
                <div style={{ color: 'var(--text-muted)' }}>Timeframe: {generatedStrategy.timeframe}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Strategy Library */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Strategy Library ({strategies.length})</h4>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Strategy Name</th>
              <th>Timeframe</th>
              <th>Entry Rules</th>
              <th>Risk/Reward</th>
              <th style={{ textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {strategies.length > 0 ? (
              strategies.map((st) => (
                <tr key={st.id}>
                  <td style={{ fontWeight: 700 }}>{st.name}</td>
                  <td><span className="badge badge-blue">{st.timeframe}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {st.entry_rules.map((r: string, i: number) => (
                        <span key={i} className="badge badge-purple" style={{ fontSize: '0.7rem' }}>{r}</span>
                      ))}
                    </div>
                  </td>
                  <td className="mono" style={{ fontSize: '0.85rem' }}>
                    SL: {st.stop_loss?.value}% / Tgt: {st.target?.value}%
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => navigate('/backtests', { state: { strategy: st } })}
                      className="btn btn-primary"
                      style={{ padding: '4px 10px', fontSize: '0.75rem', gap: '4px' }}
                    >
                      <Play size={12} />
                      <span>Backtest</span>
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No custom strategies saved yet. Use the AI generator above to build your first strategy!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
