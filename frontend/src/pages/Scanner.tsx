import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { Scan, Sparkles, Play, CheckCircle2, Zap } from 'lucide-react';

export const Scanner: React.FC = () => {
  const { showToast } = useToast();
  const [presets, setPresets] = useState<any[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('');
  const [nlQuery, setNlQuery] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [activeRules, setActiveRules] = useState<any[]>([]);

  useEffect(() => {
    ApiClient.getScannerPresets().then((p) => {
      setPresets(p);
      if (p.length > 0) {
        setSelectedPresetId(p[0].id);
        setActiveRules(p[0].rules);
      }
    });
  }, []);

  const handleSelectPreset = (p: any) => {
    setSelectedPresetId(p.id);
    setActiveRules(p.rules);
  };

  const handleRunScan = async (rulesToRun?: any[]) => {
    const rules = rulesToRun || activeRules;
    if (!rules || rules.length === 0) return;
    setIsScanning(true);
    try {
      const data = await ApiClient.runScanner(rules);
      setResults(data);
      showToast(`Scan complete. Found ${data.length} matching stocks`, 'success');
    } catch (err: any) {
      showToast(err.message || 'Scan failed', 'error');
    } finally {
      setIsScanning(false);
    }
  };

  const handleTranslateNL = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlQuery.trim()) return;
    setIsTranslating(true);
    try {
      const parsed = await ApiClient.parseNLScanner(nlQuery);
      setActiveRules(parsed.rules);
      setSelectedPresetId('custom');
      showToast('AI successfully translated prompt into structured scanner rules', 'info');
      handleRunScan(parsed.rules);
    } catch (err: any) {
      showToast(err.message, 'error');
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Quantitative Market Scanner</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Scan the entire Indian market using mathematical indicators or natural language queries
        </p>
      </div>

      {/* Natural Language Prompt Card */}
      <div className="card card-glow-purple">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Sparkles size={18} color="var(--accent-purple)" />
          <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>AI Natural Language Scanner</h4>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
          Type any technical condition in plain English. The AI parses indicator filters deterministically.
        </p>
        <form onSubmit={handleTranslateNL} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            placeholder="e.g. Find Indian stocks with price above 20 EMA, RSI between 50 and 70, and volume spike"
            value={nlQuery}
            onChange={(e) => setNlQuery(e.target.value)}
            className="input"
            style={{ flex: 1 }}
          />
          <button type="submit" disabled={isTranslating} className="btn btn-purple" style={{ whiteSpace: 'nowrap' }}>
            <Sparkles size={16} />
            <span>{isTranslating ? 'Translating...' : 'Translate & Scan'}</span>
          </button>
        </form>
      </div>

      {/* Preset Filters Row */}
      <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '4px' }}>
        {presets.map((p) => (
          <button
            key={p.id}
            onClick={() => { handleSelectPreset(p); handleRunScan(p.rules); }}
            className={`btn ${selectedPresetId === p.id ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '8px 16px', borderRadius: '10px' }}
          >
            {p.name}
          </button>
        ))}
      </div>

      {/* Active Rules Display & Run Button */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Active Filter Conditions:</span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {activeRules.map((r, i) => (
              <span key={i} className="badge badge-blue">
                {r.indicator} {r.operator} {Array.isArray(r.value) ? r.value.join('..') : r.value}
              </span>
            ))}
          </div>
        </div>

        <button onClick={() => handleRunScan()} disabled={isScanning} className="btn btn-primary" style={{ padding: '8px 20px' }}>
          <Play size={16} />
          <span>{isScanning ? 'Scanning...' : 'Run Scanner'}</span>
        </button>
      </div>

      {/* Scan Results Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Matching Equities ({results.length})</h4>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Filtered from NSE Universe</span>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Stock</th>
              <th style={{ textAlign: 'right' }}>Price (INR)</th>
              <th style={{ textAlign: 'right' }}>Day Change</th>
              <th>Matched Signal Conditions</th>
              <th style={{ textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {results.length > 0 ? (
              results.map((res) => (
                <tr key={res.symbol}>
                  <td>
                    <Link to={`/stock/${res.symbol}`} style={{ textDecoration: 'none', color: '#fff' }}>
                      <div style={{ fontWeight: 700 }}>{res.symbol}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{res.name}</div>
                    </Link>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className="mono tabular-nums" style={{ fontWeight: 700 }}>
                      ₹{Number(res.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={Number(res.change_pct) >= 0 ? 'text-profit mono' : 'text-loss mono'}>
                      {Number(res.change_pct) >= 0 ? '+' : ''}{Number(res.change_pct).toFixed(2)}%
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {res.matched_conditions.map((mc: string, idx: number) => (
                        <span key={idx} className="badge badge-green" style={{ fontSize: '0.7rem' }}>
                          ✓ {mc}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <Link to={`/stock/${res.symbol}`} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                      Analyze
                    </Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  {isScanning ? 'Scanning Indian market indicators...' : 'Select a preset or enter a query above and click "Run Scanner".'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
