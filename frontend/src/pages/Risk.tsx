import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { ShieldAlert, AlertTriangle, Power, Save, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

export const Risk: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [killSwitches, setKillSwitches] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Form state
  const [maxOrderValue, setMaxOrderValue] = useState<number>(500000);
  const [maxDailyLoss, setMaxDailyLoss] = useState<number>(25000);
  const [maxPositionValue, setMaxPositionValue] = useState<number>(200000);
  const [maxOpenPositions, setMaxOpenPositions] = useState<number>(10);
  const [maxQuantity, setMaxQuantity] = useState<number>(500);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sData, ksData, eData] = await Promise.all([
        ApiClient.getRiskSettings(),
        ApiClient.getKillSwitches(),
        ApiClient.getRiskEvents(25)
      ]);
      setSettings(sData);
      setKillSwitches(ksData);
      setEvents(eData);

      setMaxOrderValue(sData.max_order_value);
      setMaxDailyLoss(sData.max_daily_loss);
      setMaxPositionValue(sData.max_position_value);
      setMaxOpenPositions(sData.max_open_positions);
      setMaxQuantity(sData.max_quantity);
    } catch (err: any) {
      console.error('Error fetching risk data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await ApiClient.updateRiskSettings({
        max_order_value: Number(maxOrderValue),
        max_daily_loss: Number(maxDailyLoss),
        max_position_value: Number(maxPositionValue),
        max_open_positions: Number(maxOpenPositions),
        max_quantity: Number(maxQuantity)
      });
      setMessage({ text: 'Risk settings updated successfully', type: 'success' });
      fetchData();
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to save risk settings', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleToggleKillSwitch = async (scope: 'USER' | 'AI_TRADING', currentActive: boolean) => {
    try {
      await ApiClient.toggleKillSwitch(scope, !currentActive, `${scope} Kill Switch ${!currentActive ? 'Engaged' : 'Disengaged'} via UI`);
      setMessage({
        text: `${scope} Kill Switch ${!currentActive ? 'ACTIVATED: Trading Blocked' : 'DEACTIVATED: Trading Allowed'}`,
        type: !currentActive ? 'error' : 'success'
      });
      fetchData();
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to toggle kill switch', type: 'error' });
    }
  };

  const userKillSwitch = killSwitches.find((k) => k.scope === 'USER');
  const aiKillSwitch = killSwitches.find((k) => k.scope === 'AI_TRADING');
  const platformKillSwitch = killSwitches.find((k) => k.scope === 'PLATFORM');

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={28} color="#ef4444" />
            Deterministic Risk Engine & Kill Switches
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px', fontSize: '0.95rem' }}>
            Authoritative risk controls, loss governors, and operational emergency brakes.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="btn btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh Status
        </button>
      </div>

      {message && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: message.type === 'success' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          color: message.type === 'success' ? '#4ade80' : '#f87171',
          border: `1px solid ${message.type === 'success' ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
        }}>
          {message.type === 'success' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
          <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{message.text}</span>
        </div>
      )}

      {/* Kill Switches Panel */}
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)' }}>
          Emergency Kill Switches
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {/* User Emergency Stop */}
          <div className="card" style={{
            padding: '1.5rem',
            border: userKillSwitch?.is_active ? '2px solid #ef4444' : '1px solid var(--border)',
            background: userKillSwitch?.is_active ? 'rgba(239, 68, 68, 0.08)' : 'var(--surface)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span className={`badge ${userKillSwitch?.is_active ? 'badge-rose' : 'badge-green'}`} style={{ marginBottom: '8px' }}>
                  {userKillSwitch?.is_active ? 'ACTIVE • TRADING BLOCKED' : 'INACTIVE • TRADING ALLOWED'}
                </span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                  User Kill Switch
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Instantly halt all order execution across manual paper, sandbox, and live trading.
                </p>
              </div>
              <button
                onClick={() => handleToggleKillSwitch('USER', Boolean(userKillSwitch?.is_active))}
                className={`btn ${userKillSwitch?.is_active ? 'btn-secondary' : 'btn-danger'}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: 700,
                  padding: '10px 16px',
                  background: userKillSwitch?.is_active ? '#334155' : '#ef4444',
                  color: '#fff'
                }}
              >
                <Power size={18} />
                {userKillSwitch?.is_active ? 'DISENGAGE' : 'STOP ALL TRADING'}
              </button>
            </div>
          </div>

          {/* AI Auto-Trading Kill Switch */}
          <div className="card" style={{
            padding: '1.5rem',
            border: aiKillSwitch?.is_active ? '2px solid #f59e0b' : '1px solid var(--border)',
            background: aiKillSwitch?.is_active ? 'rgba(245, 158, 11, 0.08)' : 'var(--surface)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span className={`badge ${aiKillSwitch?.is_active ? 'badge-amber' : 'badge-green'}`} style={{ marginBottom: '8px' }}>
                  {aiKillSwitch?.is_active ? 'HALTED • AI ORDERS BLOCKED' : 'READY • AUTOMATION ARMED'}
                </span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                  AI Trading Kill Switch
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Halt all automated signals generated by AI without affecting manual trading.
                </p>
              </div>
              <button
                onClick={() => handleToggleKillSwitch('AI_TRADING', Boolean(aiKillSwitch?.is_active))}
                className="btn btn-secondary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: 700,
                  padding: '10px 16px',
                  background: aiKillSwitch?.is_active ? '#334155' : '#d97706',
                  color: '#fff'
                }}
              >
                <Power size={18} />
                {aiKillSwitch?.is_active ? 'RESUME AI' : 'HALT AI TRADING'}
              </button>
            </div>
          </div>

          {/* Platform Operational Status */}
          <div className="card" style={{ padding: '1.5rem', background: 'var(--surface)' }}>
            <div>
              <span className={`badge ${platformKillSwitch?.is_active ? 'badge-rose' : 'badge-green'}`} style={{ marginBottom: '8px' }}>
                {platformKillSwitch?.is_active ? 'PLATFORM EMERGENCY' : 'PLATFORM NORMAL'}
              </span>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                Platform Operational Switch
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Global circuit breaker controlled by platform administrators for market wide risk containment.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Persistent Limits Form */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>
        <div className="card" style={{ padding: '1.75rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem', color: 'var(--text-primary)' }}>
            Persistent Risk Limits & Governors
          </h2>
          <form onSubmit={handleSaveSettings} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Maximum Order Value (₹)
              </label>
              <input
                type="number"
                value={maxOrderValue}
                onChange={(e) => setMaxOrderValue(Number(e.target.value))}
                min={1000}
                max={5000000}
                className="input"
                style={{ width: '100%' }}
                required
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Orders exceeding this gross turnover will be rejected.</span>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Maximum Daily Loss Limit (₹)
              </label>
              <input
                type="number"
                value={maxDailyLoss}
                onChange={(e) => setMaxDailyLoss(Number(e.target.value))}
                min={1000}
                max={1000000}
                className="input"
                style={{ width: '100%' }}
                required
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Trading blocked when day's net loss exceeds this threshold.</span>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Maximum Position Value (₹)
              </label>
              <input
                type="number"
                value={maxPositionValue}
                onChange={(e) => setMaxPositionValue(Number(e.target.value))}
                min={1000}
                max={5000000}
                className="input"
                style={{ width: '100%' }}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Max Open Positions
                </label>
                <input
                  type="number"
                  value={maxOpenPositions}
                  onChange={(e) => setMaxOpenPositions(Number(e.target.value))}
                  min={1}
                  max={50}
                  className="input"
                  style={{ width: '100%' }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Max Quantity / Order
                </label>
                <input
                  type="number"
                  value={maxQuantity}
                  onChange={(e) => setMaxQuantity(Number(e.target.value))}
                  min={1}
                  max={10000}
                  className="input"
                  style={{ width: '100%' }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginTop: '0.5rem' }}
            >
              <Save size={18} />
              {saving ? 'Saving Limits...' : 'Save Risk Parameters'}
            </button>
          </form>
        </div>

        {/* Deterministic Validation Rules Info */}
        <div className="card" style={{ padding: '1.75rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem', color: 'var(--text-primary)' }}>
            Mandatory Validation Pipeline
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(37, 99, 235, 0.2)', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>1</div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>Exchange & Session Rules</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>NSE trading session validation (09:15 - 15:30 IST) & 0.05 tick size enforcement.</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(37, 99, 235, 0.2)', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>2</div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>Anti-Overselling & Capital Protection</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Never allows negative positions or overselling; BUY orders strictly validated against available balance.</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(37, 99, 235, 0.2)', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>3</div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>Data Freshness & Circuit Bounds</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Rejects stale quotes (&gt;45s age) and verifies limit price falls within circuit bounds.</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(37, 99, 235, 0.2)', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>4</div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>Duplicate Order Velocity Guard</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Blocks identical orders submitted within 5 seconds to prevent accidental double fills.</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(37, 99, 235, 0.2)', color: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>5</div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>Risk-to-Reward Ratio</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Enforces minimum Risk/Reward ratio of 0.5:1 when SL and Target are provided.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Risk Events Audit Table */}
      <div className="card" style={{ padding: '1.75rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem', color: 'var(--text-primary)' }}>
          Risk Engine Block & Audit Events
        </h2>
        {events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No risk violations or blocked orders recorded.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 12px' }}>Timestamp</th>
                  <th style={{ padding: '10px 12px' }}>Symbol</th>
                  <th style={{ padding: '10px 12px' }}>Side</th>
                  <th style={{ padding: '10px 12px' }}>Check Failed</th>
                  <th style={{ padding: '10px 12px' }}>Rejection Reason</th>
                  <th style={{ padding: '10px 12px' }}>Severity</th>
                </tr>
              </thead>
              <tbody>
                {events.map((evt) => (
                  <tr key={evt.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '10px 12px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {new Date(evt.created_at).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {evt.symbol}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className={`badge ${evt.side === 'BUY' ? 'badge-green' : 'badge-rose'}`}>
                        {evt.side}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: '#f87171' }}>
                      {evt.check_name}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>
                      {evt.rejection_reason}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className="badge badge-rose">
                        {evt.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
