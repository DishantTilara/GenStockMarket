import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { Bell, Plus, Trash2, AlertCircle, CheckCircle2 } from 'lucide-react';

export const Alerts: React.FC = () => {
  const { showToast } = useToast();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);

  const [symbol, setSymbol] = useState('RELIANCE');
  const [conditionType, setConditionType] = useState('PRICE_ABOVE');
  const [targetValue, setTargetValue] = useState('3050');

  const fetchAlerts = async () => {
    try {
      const data = await ApiClient.getAlerts();
      setAlerts(data);
      const hist = await ApiClient.request<any[]>('/alerts/history');
      setHistory(hist);
    } catch {}
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(targetValue);
    if (!val) return;
    try {
      await ApiClient.createAlert(symbol.toUpperCase(), conditionType, val);
      showToast(`Alert set for ${symbol.toUpperCase()}`, 'success');
      setIsCreating(false);
      fetchAlerts();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const handleDeleteAlert = async (id: string) => {
    try {
      await ApiClient.deleteAlert(id);
      showToast('Alert removed', 'info');
      fetchAlerts();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Price & Technical Alerts</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Real-time automated alerts for price breaks, RSI extremes, and volume surges
          </p>
        </div>

        <button onClick={() => setIsCreating(true)} className="btn btn-primary">
          <Plus size={16} />
          <span>New Alert</span>
        </button>
      </div>

      {/* Create Alert Modal / Form */}
      {isCreating && (
        <form onSubmit={handleCreateAlert} className="card" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr) auto', gap: '12px', alignItems: 'end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="input"
              placeholder="e.g. TCS"
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Condition</label>
            <select
              value={conditionType}
              onChange={(e) => setConditionType(e.target.value)}
              className="input"
            >
              <option value="PRICE_ABOVE">Price Above (₹)</option>
              <option value="PRICE_BELOW">Price Below (₹)</option>
              <option value="RSI_OVERBOUGHT">RSI Overbought (&gt;=)</option>
              <option value="RSI_OVERSOLD">RSI Oversold (&lt;=)</option>
              <option value="VOLUME_SPIKE">Volume Spike Surge</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Target Value</label>
            <input
              type="number"
              value={targetValue}
              onChange={(e) => setTargetValue(e.target.value)}
              className="input mono"
              placeholder="3050"
              step="any"
              required
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Save Alert</button>
            <button type="button" onClick={() => setIsCreating(false)} className="btn btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      {/* Active Alerts List */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Active Alert Monitors ({alerts.length})</h4>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Trigger Condition</th>
              <th>Target Value</th>
              <th>Status</th>
              <th style={{ textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length > 0 ? (
              alerts.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontWeight: 700 }}>{a.symbol}</td>
                  <td>
                    <span className="badge badge-blue">{a.condition_type.replace('_', ' ')}</span>
                  </td>
                  <td className="mono font-bold">
                    {a.condition_type.includes('PRICE') ? `₹${Number(a.target_value).toFixed(2)}` : a.target_value}
                  </td>
                  <td>
                    {a.is_triggered ? (
                      <span className="badge badge-amber">Triggered</span>
                    ) : (
                      <span className="badge badge-green">Listening</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => handleDeleteAlert(a.id)}
                      style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                      title="Delete alert"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No active alerts. Click "New Alert" to configure price or RSI triggers.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Triggered Events History */}
      <div className="card">
        <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px' }}>Alert Trigger Log</h4>
        {history.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {history.map((h) => (
              <div key={h.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <AlertCircle size={18} color="var(--accent-amber)" />
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{h.message}</span>
                </div>
                <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {new Date(h.triggered_at).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No alert triggers recorded in this session.</div>
        )}
      </div>
    </div>
  );
};
