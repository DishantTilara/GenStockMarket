import React, { useState, useEffect } from 'react';
import {
  Server,
  ShieldCheck,
  Key,
  Lock,
  RefreshCw,
  Power,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Layers,
  DollarSign
} from 'lucide-react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';

export const Broker: React.FC = () => {
  const { showToast } = useToast();
  const [loading, setLoading] = useState<boolean>(true);
  const [statusData, setStatusData] = useState<any>(null);
  const [envData, setEnvData] = useState<any>(null);
  const [margins, setMargins] = useState<any>(null);

  // Form State
  const [brokerName, setBrokerName] = useState<string>('sandbox');
  const [environment, setEnvironment] = useState<string>('SANDBOX');
  const [apiKey, setApiKey] = useState<string>('');
  const [apiSecret, setApiSecret] = useState<string>('');
  const [clientId, setClientId] = useState<string>('');
  const [connecting, setConnecting] = useState<boolean>(false);

  // Reconciliation State
  const [reconciliationData, setReconciliationData] = useState<any>(null);
  const [reconciliationEvents, setReconciliationEvents] = useState<any[]>([]);
  const [reconciling, setReconciling] = useState<boolean>(false);

  const fetchBrokerDetails = async () => {
    try {
      setLoading(true);
      const [statusRes, envRes, marginRes, recEventsRes] = await Promise.all([
        ApiClient.getBrokerStatus().catch(() => null),
        ApiClient.getTradingEnvironment().catch(() => null),
        ApiClient.getBrokerMargins().catch(() => null),
        ApiClient.getReconciliationEvents(20).catch(() => [])
      ]);
      setStatusData(statusRes);
      setEnvData(envRes);
      setMargins(marginRes);
      setReconciliationEvents(recEventsRes || []);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch broker status', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRunReconciliation = async () => {
    try {
      setReconciling(true);
      const res = await ApiClient.triggerReconciliation();
      setReconciliationData(res);
      showToast(
        `Reconciliation complete: ${res.discrepancies_detected} discrepancies, ${res.corrections_applied} corrections applied`,
        res.discrepancies_detected > 0 ? 'info' : 'success'
      );
      await fetchBrokerDetails();
    } catch (err: any) {
      showToast(err.message || 'Reconciliation failed', 'error');
    } finally {
      setReconciling(false);
    }
  };

  useEffect(() => {
    fetchBrokerDetails();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey || !apiSecret) {
      showToast('Please provide both API Key and API Secret', 'error');
      return;
    }

    try {
      setConnecting(true);
      await ApiClient.connectBroker({
        broker_name: brokerName,
        environment,
        api_key: apiKey,
        api_secret: apiSecret,
        client_id: clientId || undefined
      });
      showToast('Broker connected securely. Credentials encrypted at rest.', 'success');
      setApiKey('');
      setApiSecret('');
      await fetchBrokerDetails();
    } catch (err: any) {
      showToast(err.message || 'Broker connection failed', 'error');
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await ApiClient.disconnectBroker();
      showToast('Broker gateway disconnected', 'info');
      await fetchBrokerDetails();
    } catch (err: any) {
      showToast(err.message || 'Failed to disconnect broker', 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto', paddingBottom: '3rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Server style={{ color: 'var(--accent-blue)' }} size={28} />
            Broker Gateway & Execution Engine
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            Connect Indian Exchange Broker APIs (Zerodha Kite Connect, Angel One, Upstox) or Sandbox Simulator with AES-encrypted credential vault.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            padding: '4px 12px',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 700,
            background: envData?.is_live ? 'rgba(239, 68, 68, 0.15)' : 'rgba(59, 130, 246, 0.15)',
            border: envData?.is_live ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(59, 130, 246, 0.4)',
            color: envData?.is_live ? '#ef4444' : '#60a5fa'
          }}>
            {envData?.trading_mode || 'PAPER'} MODE ACTIVE
          </span>
          <button
            onClick={fetchBrokerDetails}
            style={{
              padding: '8px 14px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Sync
          </button>
        </div>
      </div>

      {/* Grid: Status & Margins */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Gateway Connection Card */}
        <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Gateway Status
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {statusData?.is_connected ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981', fontSize: '0.8rem', fontWeight: 600 }}>
                  <CheckCircle2 size={16} /> CONNECTED
                </span>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b', fontSize: '0.8rem', fontWeight: 600 }}>
                  <AlertTriangle size={16} /> DISCONNECTED
                </span>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Broker Adapter:</span>
              <span style={{ fontWeight: 600, color: '#fff', textTransform: 'uppercase' }}>{statusData?.broker_name || 'SANDBOX'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Client ID:</span>
              <span style={{ fontWeight: 600, color: '#fff' }}>{statusData?.client_id || 'N/A'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>API Key:</span>
              <span style={{ fontWeight: 600, color: '#fff', fontFamily: 'monospace' }}>{statusData?.api_key_masked || 'None Configured'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Token Expiry:</span>
              <span style={{ fontWeight: 600, color: '#fff' }}>
                {statusData?.token_expires_at ? new Date(statusData.token_expires_at).toLocaleTimeString() : 'Session Active'}
              </span>
            </div>
          </div>

          {statusData?.has_account && (
            <button
              onClick={handleDisconnect}
              style={{
                marginTop: '0.5rem',
                padding: '8px 16px',
                borderRadius: '8px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#ef4444',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              <Power size={16} /> Disconnect Gateway
            </button>
          )}
        </div>

        {/* Real-time Margins Card */}
        <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Broker Margin & Capital
          </span>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Cash Balance</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginTop: '2px' }}>
                ₹{margins?.cash_balance ? margins.cash_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
              </div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(16, 185, 129, 0.05)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: '#10b981' }}>Available Margin</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#10b981', marginTop: '2px' }}>
                ₹{margins?.available_margin ? margins.available_margin.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
              </div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Used Margin</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginTop: '2px' }}>
                ₹{margins?.used_margin ? margins.used_margin.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
              </div>
            </div>

            <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Collateral</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginTop: '2px' }}>
                ₹0.00
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Connect Form */}
      <div className="card" style={{ padding: '1.75rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Key size={18} style={{ color: 'var(--accent-blue)' }} /> Connect Broker API Credentials
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Secrets are symmetrically encrypted at rest using AES-GCM and never returned via API responses or printed in server logs.
        </p>

        <form onSubmit={handleConnect} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Broker Gateway
            </label>
            <select
              value={brokerName}
              onChange={(e) => setBrokerName(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                color: '#fff',
                fontSize: '0.875rem'
              }}
            >
              <option value="sandbox">Sandbox Simulator</option>
              <option value="zerodha">Zerodha Kite Connect</option>
              <option value="angelone">Angel One SmartAPI</option>
              <option value="upstox">Upstox Pro API</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Environment
            </label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                color: '#fff',
                fontSize: '0.875rem'
              }}
            >
              <option value="SANDBOX">SANDBOX (Simulation)</option>
              <option value="LIVE">LIVE (Exchange Real Capital)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Client ID / UCC
            </label>
            <input
              type="text"
              placeholder="e.g. ZER12345"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
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
              API Key
            </label>
            <input
              type="text"
              placeholder="API Key from developer portal"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
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

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              API Secret / App Secret
            </label>
            <input
              type="password"
              placeholder="••••••••••••••••"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
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

          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button
              type="submit"
              disabled={connecting}
              style={{
                padding: '10px 24px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                color: '#fff',
                fontWeight: 600,
                border: 'none',
                cursor: connecting ? 'not-allowed' : 'pointer',
                opacity: connecting ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Lock size={16} />
              {connecting ? 'Encrypting & Connecting...' : 'Connect Broker Securely'}
            </button>
          </div>
        </form>
      </div>

      {/* Reconciliation Engine Card */}
      <div className="card" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} style={{ color: 'var(--accent-green)' }} />
              State Reconciliation Engine
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Continuously synchronizes and validates broker executions, positions, and balances against PostgreSQL authoritative truth.
            </p>
          </div>

          <button
            onClick={handleRunReconciliation}
            disabled={reconciling}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              color: '#10b981',
              fontWeight: 600,
              cursor: reconciling ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <RefreshCw size={16} className={reconciling ? 'animate-spin' : ''} />
            {reconciling ? 'Reconciling State...' : 'Run Reconciliation Check'}
          </button>
        </div>

        {reconciliationData && (
          <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status:</span>
                <div style={{ fontWeight: 700, color: '#10b981' }}>{reconciliationData.status}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Discrepancies Detected:</span>
                <div style={{ fontWeight: 700, color: reconciliationData.discrepancies_detected > 0 ? '#f59e0b' : '#fff' }}>
                  {reconciliationData.discrepancies_detected}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Auto-Corrections Applied:</span>
                <div style={{ fontWeight: 700, color: '#10b981' }}>{reconciliationData.corrections_applied}</div>
              </div>
            </div>
          </div>
        )}

        {/* Reconciliation Events History Table */}
        <div>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Reconciliation Audit History
          </h4>

          {reconciliationEvents.length === 0 ? (
            <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No discrepancies detected. Internal database and broker gateway are fully synchronized.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '8px 12px' }}>Timestamp</th>
                    <th style={{ padding: '8px 12px' }}>Discrepancy Type</th>
                    <th style={{ padding: '8px 12px' }}>Resolution Notes</th>
                    <th style={{ padding: '8px 12px' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {reconciliationEvents.map((evt) => (
                    <tr key={evt.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>
                        {new Date(evt.created_at).toLocaleTimeString()}
                      </td>
                      <td style={{ padding: '8px 12px', fontWeight: 600, color: '#f59e0b' }}>
                        {evt.discrepancy_type}
                      </td>
                      <td style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>
                        {evt.resolution_notes || 'Pending automatic cycle'}
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          background: evt.resolved ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                          color: evt.resolved ? '#10b981' : '#ef4444'
                        }}>
                          {evt.resolved ? 'RESOLVED' : 'UNRESOLVED'}
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
    </div>
  );
};
export default Broker;

