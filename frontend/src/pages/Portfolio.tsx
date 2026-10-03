import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import {
  Briefcase,
  PieChart,
  ShieldAlert,
  TrendingUp,
  TrendingDown,
  RotateCcw,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  DollarSign,
  AlertTriangle
} from 'lucide-react';

export const Portfolio: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [portfolio, setPortfolio] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'HOLDINGS' | 'ALLOCATION' | 'PERFORMANCE' | 'RISK'>('HOLDINGS');
  const [isResetting, setIsResetting] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);

  const fetchPortfolio = async () => {
    try {
      const [p, a] = await Promise.all([
        ApiClient.getPortfolio(),
        ApiClient.getPortfolioAnalysis().catch(() => null)
      ]);
      setPortfolio(p);
      if (a) setAnalysis(a);
    } catch {}
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const handleReset = async () => {
    try {
      setIsResetting(true);
      await ApiClient.resetPaperAccount({
        starting_capital: 1000000,
        confirm: true,
        clear_orders: true
      });
      showToast('Paper account reset successfully to ₹10,00,000.00 cash.', 'success');
      setConfirmReset(false);
      fetchPortfolio();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to reset paper account', 'error');
    } finally {
      setIsResetting(false);
    }
  };

  const totalValue = portfolio ? Number(portfolio.total_equity) : 1000000;
  const invested = portfolio ? Number(portfolio.total_invested) : 0;
  const cash = portfolio ? Number(portfolio.cash_balance) : 1000000;
  const positionsVal = portfolio ? Number(portfolio.current_value) : 0;
  const unrealizedPnl = portfolio ? Number(portfolio.total_unrealized_pnl) : 0;
  const unrealizedPct = portfolio ? Number(portfolio.total_unrealized_pnl_pct) : 0;
  const realizedPnl = portfolio ? Number(portfolio.realized_pnl || 0) : 0;
  const overallPnl = portfolio ? Number(portfolio.total_pnl || 0) : (unrealizedPnl + realizedPnl);
  const todayPnl = portfolio ? Number(portfolio.today_pnl || 0) : unrealizedPnl * 0.35;
  const todayPct = portfolio ? Number(portfolio.today_pnl_pct || 0) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner: Paper Disclosure & Reset */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1.25rem',
        background: 'var(--surface)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        flexWrap: 'wrap',
        gap: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="paper-badge">PAPER PORTFOLIO</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Simulated Indian Equity Holdings • Zero real capital at risk
          </span>
        </div>

        <div>
          {!confirmReset ? (
            <button
              onClick={() => setConfirmReset(true)}
              className="btn btn-secondary"
              style={{ padding: '5px 12px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <RotateCcw size={13} />
              <span>Reset Paper Account</span>
            </button>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--loss)', fontWeight: 600 }}>Reset to ₹10L cash?</span>
              <button
                onClick={handleReset}
                disabled={isResetting}
                className="btn btn-sell"
                style={{ padding: '4px 10px', fontSize: '0.72rem' }}
              >
                {isResetting ? 'Resetting...' : 'Yes, Reset'}
              </button>
              <button
                onClick={() => setConfirmReset(false)}
                className="btn btn-secondary"
                style={{ padding: '4px 8px', fontSize: '0.72rem' }}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Top Summary Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Portfolio Value</div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '4px' }}>
            ₹{totalValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Positions: ₹{positionsVal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Invested</div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '4px' }}>
            ₹{invested.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Available Margin: <span className="mono font-bold text-profit">₹{cash.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Today's P&L</div>
          <div className={`mono font-bold ${todayPnl >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.75rem', marginTop: '4px' }}>
            {todayPnl >= 0 ? '+' : ''}₹{todayPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Return: <span className={`mono font-bold ${todayPct >= 0 ? 'text-profit' : 'text-loss'}`}>{todayPct >= 0 ? '+' : ''}{todayPct.toFixed(2)}%</span>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Overall P&L (Total Return)</div>
          <div className={`mono font-bold ${overallPnl >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.75rem', marginTop: '4px' }}>
            {overallPnl >= 0 ? '+' : ''}₹{overallPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Unrealized: {unrealizedPnl >= 0 ? '+' : ''}₹{unrealizedPnl.toFixed(2)} | Realized: {realizedPnl >= 0 ? '+' : ''}₹{realizedPnl.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Tabs Row */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', gap: '8px' }}>
        {[
          { id: 'HOLDINGS', label: `Holdings (${portfolio?.positions?.length || 0})`, icon: Briefcase },
          { id: 'ALLOCATION', label: 'Sector Allocation', icon: PieChart },
          { id: 'PERFORMANCE', label: 'P&L Breakdown', icon: BarChart3 },
          { id: 'RISK', label: 'Risk Review', icon: ShieldAlert },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className="btn"
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid var(--primary)' : '2px solid transparent',
                borderRadius: '0',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: isActive ? 700 : 500,
                padding: '0.75rem 1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.85rem'
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Holdings Table */}
      {activeTab === 'HOLDINGS' && (
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Security</th>
                <th>Sector</th>
                <th style={{ textAlign: 'right' }}>Qty</th>
                <th style={{ textAlign: 'right' }}>Avg Price (₹)</th>
                <th style={{ textAlign: 'right' }}>LTP (₹)</th>
                <th style={{ textAlign: 'right' }}>Invested (₹)</th>
                <th style={{ textAlign: 'right' }}>Current Value (₹)</th>
                <th style={{ textAlign: 'right' }}>Unrealized P&L</th>
                <th style={{ textAlign: 'center' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {portfolio?.positions && portfolio.positions.length > 0 ? (
                portfolio.positions.map((p: any) => {
                  const isProfit = Number(p.unrealized_pnl) >= 0;
                  return (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 700 }}>
                        <Link to={`/stock/${p.symbol}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                          {p.symbol}
                        </Link>
                      </td>
                      <td><span className="badge badge-blue">{p.sector || 'Equity'}</span></td>
                      <td style={{ textAlign: 'right' }} className="mono">{p.quantity}</td>
                      <td style={{ textAlign: 'right' }} className="mono">₹{Number(p.average_price).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }} className="mono font-bold">₹{Number(p.current_price).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }} className="mono">₹{Number(p.invested_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td style={{ textAlign: 'right' }} className="mono font-bold">₹{Number(p.current_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td style={{ textAlign: 'right' }} className={isProfit ? 'text-profit mono font-bold' : 'text-loss mono font-bold'}>
                        {isProfit ? '+' : ''}₹{Number(p.unrealized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })} ({isProfit ? '+' : ''}{Number(p.unrealized_pnl_pct).toFixed(2)}%)
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => navigate('/positions')}
                          className="btn btn-secondary"
                          style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                        >
                          Manage Position →
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No active holdings. Place a paper BUY order to start building your simulated portfolio.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Sector Allocation */}
      {activeTab === 'ALLOCATION' && (
        <div className="card">
          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px' }}>Sector Allocation Breakdown</h4>
          {portfolio?.sector_allocation && Object.keys(portfolio.sector_allocation).length > 0 ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
              {Object.entries(portfolio.sector_allocation).map(([sector, pct]: [string, any]) => (
                <div key={sector} style={{ background: 'var(--surface-muted)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{sector}</div>
                  <div className="mono font-bold" style={{ fontSize: '1.5rem', margin: '4px 0' }}>{Number(pct).toFixed(1)}%</div>
                  <div style={{ width: '100%', height: '6px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, Number(pct))}%`, height: '100%', background: 'var(--primary)' }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No sector allocation data available yet. Open paper positions to view diversification.
            </p>
          )}
        </div>
      )}

      {/* Tab 3: Performance & P&L Breakdown */}
      {activeTab === 'PERFORMANCE' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="card">
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '14px' }}>P&L Structure</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Starting Capital</span>
                <span className="mono font-bold">₹10,00,000.00</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Realized P&L (Exited Trades)</span>
                <span className={`mono font-bold ${realizedPnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                  {realizedPnl >= 0 ? '+' : ''}₹{realizedPnl.toFixed(2)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Unrealized P&L (Open MTM)</span>
                <span className={`mono font-bold ${unrealizedPnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                  {unrealizedPnl >= 0 ? '+' : ''}₹{unrealizedPnl.toFixed(2)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Available Paper Cash</span>
                <span className="mono font-bold">₹{cash.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', fontWeight: 700 }}>
                <span style={{ fontSize: '0.9rem' }}>Net Portfolio Equity</span>
                <span className="mono font-bold text-profit" style={{ fontSize: '1.1rem' }}>
                  ₹{totalValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>

          <div className="card">
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '14px' }}>Deterministic Performance Metrics</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Portfolio ROI</span>
                <span className={`mono font-bold ${totalValue >= 1000000 ? 'text-profit' : 'text-loss'}`}>
                  {(((totalValue - 1000000) / 1000000) * 100).toFixed(2)}%
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Positions Count</span>
                <span className="mono font-bold">{portfolio?.positions?.length || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Cash Deployment Ratio</span>
                <span className="mono font-bold">
                  {totalValue > 0 ? ((positionsVal / totalValue) * 100).toFixed(1) : 0}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Risk Review */}
      {activeTab === 'RISK' && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <ShieldAlert size={18} color="var(--primary)" />
            <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Deterministic Risk Engine Assessment</h4>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            {analysis?.summary || 'Auditing active positions against maximum single-stock exposure and portfolio limits.'}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <h5 style={{ fontSize: '0.8rem', color: 'var(--loss)', marginBottom: '8px' }}>Concentration Warnings</h5>
              {analysis?.concentration_risks && analysis.concentration_risks.length > 0 ? (
                <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {analysis.concentration_risks.map((c: string, idx: number) => <li key={idx}>{c}</li>)}
                </ul>
              ) : (
                <p style={{ fontSize: '0.8rem', color: 'var(--profit)' }}>✓ No concentration limit violations detected.</p>
              )}
            </div>

            <div>
              <h5 style={{ fontSize: '0.8rem', color: 'var(--profit)', marginBottom: '8px' }}>Diversification Observations</h5>
              {analysis?.diversification_observations && analysis.diversification_observations.length > 0 ? (
                <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {analysis.diversification_observations.map((d: string, idx: number) => <li key={idx}>{d}</li>)}
                </ul>
              ) : (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No warnings.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
