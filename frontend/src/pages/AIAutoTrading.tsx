import React, { useState, useEffect } from 'react';
import {
  Bot,
  ShieldAlert,
  Power,
  Sliders,
  Clock,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  Save,
  Tag,
  ShieldCheck,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';

export const AIAutoTrading: React.FC = () => {
  const { showToast } = useToast();
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [stopping, setStopping] = useState<boolean>(false);

  // Settings state
  const [autoTradingEnabled, setAutoTradingEnabled] = useState<boolean>(false);
  const [autoBuyEnabled, setAutoBuyEnabled] = useState<boolean>(false);
  const [autoSellEnabled, setAutoSellEnabled] = useState<boolean>(false);
  const [requireRiskApproval, setRequireRiskApproval] = useState<boolean>(true);
  const [maxOrderValue, setMaxOrderValue] = useState<number>(50000);
  const [maxDailyLoss, setMaxDailyLoss] = useState<number>(15000);
  const [maxPositionValue, setMaxPositionValue] = useState<number>(100000);
  const [maxOpenPositions, setMaxOpenPositions] = useState<number>(5);
  const [maxDailyOrders, setMaxDailyOrders] = useState<number>(20);
  const [allowedSymbols, setAllowedSymbols] = useState<string[]>(['RELIANCE', 'TCS', 'INFY']);
  const [newSymbol, setNewSymbol] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('09:15');
  const [endTime, setEndTime] = useState<string>('15:15');
  const [killSwitchActive, setKillSwitchActive] = useState<boolean>(false);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getAIAutoTradingSettings();
      setAutoTradingEnabled(data.auto_trading_enabled);
      setAutoBuyEnabled(data.auto_buy_enabled);
      setAutoSellEnabled(data.auto_sell_enabled);
      setRequireRiskApproval(data.require_risk_approval);
      setMaxOrderValue(data.max_order_value);
      setMaxDailyLoss(data.max_daily_loss);
      setMaxPositionValue(data.max_position_value);
      setMaxOpenPositions(data.max_open_positions);
      setMaxDailyOrders(data.max_daily_orders);
      setAllowedSymbols(data.allowed_symbols || []);
      setStartTime(data.start_time || '09:15');
      setEndTime(data.end_time || '15:15');
      setKillSwitchActive(data.kill_switch_enabled);
    } catch (err: any) {
      showToast(err.message || 'Failed to load AI auto trading configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await ApiClient.updateAIAutoTradingSettings({
        auto_trading_enabled: autoTradingEnabled,
        auto_buy_enabled: autoBuyEnabled,
        auto_sell_enabled: autoSellEnabled,
        require_risk_approval: requireRiskApproval,
        max_order_value: maxOrderValue,
        max_daily_loss: maxDailyLoss,
        max_position_value: maxPositionValue,
        max_open_positions: maxOpenPositions,
        max_daily_orders: maxDailyOrders,
        allowed_symbols: allowedSymbols,
        start_time: startTime,
        end_time: endTime,
        kill_switch_enabled: killSwitchActive
      });
      showToast('AI Auto-Trading configuration updated successfully', 'success');
      await fetchSettings();
    } catch (err: any) {
      showToast(err.message || 'Failed to save settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleEmergencyStop = async () => {
    if (!window.confirm('EMERGENCY STOP: Disables all AI automation immediately. Are you sure?')) {
      return;
    }
    try {
      setStopping(true);
      await ApiClient.triggerAIEmergencyStop();
      showToast('EMERGENCY STOP ACTIVATED: All AI trading automation halted!', 'error');
      await fetchSettings();
    } catch (err: any) {
      showToast(err.message || 'Emergency stop failed', 'error');
    } finally {
      setStopping(false);
    }
  };

  const addSymbol = () => {
    const s = newSymbol.trim().toUpperCase();
    if (s && !allowedSymbols.includes(s)) {
      setAllowedSymbols([...allowedSymbols, s]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (sym: string) => {
    setAllowedSymbols(allowedSymbols.filter(s => s !== sym));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto', paddingBottom: '3rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bot style={{ color: 'var(--accent-purple)' }} size={28} />
            User-Controlled AI Auto Trading
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            Deterministic, rule-gated AI execution. AI never bypasses risk or user permissions and defaults to OFF.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleEmergencyStop}
            disabled={stopping}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)',
              color: '#fff',
              fontWeight: 800,
              fontSize: '0.85rem',
              border: 'none',
              cursor: stopping ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)'
            }}
          >
            <AlertOctagon size={18} />
            EMERGENCY STOP
          </button>
        </div>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSaveSettings} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Status & Master Toggles Card */}
        <div className="card" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Master Automation Status
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
                <span style={{
                  padding: '4px 14px',
                  borderRadius: '9999px',
                  fontSize: '0.85rem',
                  fontWeight: 800,
                  background: autoTradingEnabled && !killSwitchActive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: autoTradingEnabled && !killSwitchActive ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(239, 68, 68, 0.4)',
                  color: autoTradingEnabled && !killSwitchActive ? '#10b981' : '#ef4444'
                }}>
                  {killSwitchActive ? 'EMERGENCY HALTED' : autoTradingEnabled ? 'ACTIVE [ON]' : 'DISABLED [OFF]'}
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  (Fail-closed: All trades require explicit permission + risk checks)
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setAutoTradingEnabled(!autoTradingEnabled)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  background: autoTradingEnabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  border: autoTradingEnabled ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                  color: autoTradingEnabled ? '#10b981' : '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Power size={16} />
                {autoTradingEnabled ? 'Turn OFF' : 'Turn ON'}
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginTop: '0.5rem' }}>
            {/* Automatic BUY */}
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <TrendingUp size={16} style={{ color: '#10b981' }} /> Automatic BUY
                </span>
                <input
                  type="checkbox"
                  checked={autoBuyEnabled}
                  onChange={(e) => setAutoBuyEnabled(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: '#10b981', cursor: 'pointer' }}
                />
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                Executes automated buys when AI signal action is BUY and passes risk controls.
              </p>
            </div>

            {/* Automatic SELL */}
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <TrendingDown size={16} style={{ color: '#ef4444' }} /> Automatic SELL
                </span>
                <input
                  type="checkbox"
                  checked={autoSellEnabled}
                  onChange={(e) => setAutoSellEnabled(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: '#ef4444', cursor: 'pointer' }}
                />
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                Requires active position ownership. Overselling and naked shorts are strictly blocked.
              </p>
            </div>

            {/* Risk Approval */}
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={16} style={{ color: '#3b82f6' }} /> Mandatory Risk Approval
                </span>
                <input
                  type="checkbox"
                  checked={requireRiskApproval}
                  disabled
                  style={{ width: '18px', height: '18px', accentColor: '#3b82f6', cursor: 'not-allowed' }}
                />
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                Always LOCKED [REQUIRED]. Every automatic signal must satisfy all 11 risk engine checks.
              </p>
            </div>
          </div>
        </div>

        {/* AI Exposure Limits Card */}
        <div className="card" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={18} style={{ color: 'var(--accent-purple)' }} /> AI Trading Limits & Exposure Governors
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Maximum Order Value (₹)
              </label>
              <input
                type="number"
                value={maxOrderValue}
                onChange={(e) => setMaxOrderValue(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Maximum Daily Loss Limit (₹)
              </label>
              <input
                type="number"
                value={maxDailyLoss}
                onChange={(e) => setMaxDailyLoss(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Maximum Position Value (₹)
              </label>
              <input
                type="number"
                value={maxPositionValue}
                onChange={(e) => setMaxPositionValue(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Maximum Open Positions
              </label>
              <input
                type="number"
                value={maxOpenPositions}
                onChange={(e) => setMaxOpenPositions(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Maximum Daily Orders
              </label>
              <input
                type="number"
                value={maxDailyOrders}
                onChange={(e) => setMaxDailyOrders(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-subtle)',
                  color: '#fff',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Trading Window (IST)
              </label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="text"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontSize: '0.875rem'
                  }}
                />
                <span style={{ color: 'var(--text-muted)' }}>→</span>
                <input
                  type="text"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontSize: '0.875rem'
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Allowed Symbols Whitelist */}
        <div className="card" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tag size={18} style={{ color: 'var(--accent-blue)' }} /> Whitelisted Symbols for AI Automation
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Only symbols explicitly configured in this whitelist are eligible for automatic AI signal execution.
          </p>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
            {allowedSymbols.map((sym) => (
              <span
                key={sym}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  background: 'rgba(59, 130, 246, 0.15)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  color: '#60a5fa',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {sym}
                <button
                  type="button"
                  onClick={() => removeSymbol(sym)}
                  style={{ background: 'none', border: 'none', color: '#93c5fd', cursor: 'pointer', padding: 0 }}
                >
                  ×
                </button>
              </span>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '8px', maxWidth: '360px' }}>
            <input
              type="text"
              placeholder="e.g. SBIN"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              style={{
                flex: 1,
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            />
            <button
              type="button"
              onClick={addSymbol}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid var(--border-subtle)',
                color: '#fff',
                fontSize: '0.85rem',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              Add Symbol
            </button>
          </div>
        </div>

        {/* Submit Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            type="submit"
            disabled={saving}
            style={{
              padding: '12px 28px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: '#fff',
              fontWeight: 700,
              fontSize: '0.95rem',
              border: 'none',
              cursor: saving ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(16, 185, 129, 0.3)'
            }}
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'SAVE SETTINGS'}
          </button>
        </div>
      </form>
    </div>
  );
};
export default AIAutoTrading;
