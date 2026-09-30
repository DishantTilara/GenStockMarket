import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Settings as SettingsIcon, Shield, Server, Cpu, Database, CheckCircle2 } from 'lucide-react';

export const Settings: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    ApiClient.getMarketHealth().then(setHealth).catch(() => {});
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '900px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Platform Settings & System Health</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Environment configuration, provider connectivity, and risk engine thresholds
        </p>
      </div>

      {/* User Profile */}
      <div className="card">
        <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px' }}>User Account Profile</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Name</div>
            <div style={{ fontWeight: 600 }}>{user?.full_name || 'Trader'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Email</div>
            <div style={{ fontWeight: 600 }}>{user?.email || 'trader@dalalstreet.com'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Role</div>
            <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{user?.role || 'trader'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Timezone</div>
            <div style={{ fontWeight: 600 }}>Asia/Kolkata (IST)</div>
          </div>
        </div>
      </div>

      {/* Market Ingestion Observability */}
      <div className="card">
        <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Server size={18} color="var(--accent-green)" />
          Market Data Ingestion Health
        </h4>

        {health ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }} className="mono">
            <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Provider Status</div>
              <div style={{ color: 'var(--accent-green)', fontWeight: 700, textTransform: 'uppercase' }}>
                {health.provider}
              </div>
            </div>
            <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Ingestion Lag</div>
              <div style={{ color: '#fff', fontWeight: 700 }}>{health.ingestion_lag_seconds}s</div>
            </div>
            <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Symbols Tracked</div>
              <div style={{ color: '#fff', fontWeight: 700 }}>{health.symbols_received} / {health.symbols_expected}</div>
            </div>
            <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Missing Minutes</div>
              <div style={{ color: health.missing_minutes === 0 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 700 }}>
                {health.missing_minutes} (Repaired)
              </div>
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading market telemetry...</div>
        )}
      </div>

      {/* Pre-Trade Risk Policies */}
      <div className="card">
        <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Shield size={18} color="var(--accent-blue)" />
          Risk Engine Safeguard Limits
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px' }}>
            <span>Maximum Single Order Value</span>
            <span className="mono font-bold">₹5,00,000.00</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px' }}>
            <span>Maximum Portfolio Concentration (Single Stock)</span>
            <span className="mono font-bold">25.0%</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px' }}>
            <span>Maximum Daily Loss Cutoff</span>
            <span className="mono font-bold">5.0%</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px' }}>
            <span>Mandatory Stop Loss Enforcement</span>
            <span className="badge badge-green">STRICT ENFORCEMENT</span>
          </div>
        </div>
      </div>
    </div>
  );
};
