import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { Briefcase, PieChart, ShieldAlert, TrendingUp, AlertTriangle } from 'lucide-react';

export const Portfolio: React.FC = () => {
  const [portfolio, setPortfolio] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);

  useEffect(() => {
    ApiClient.getPortfolio().then(setPortfolio).catch(() => {});
    ApiClient.getPortfolioAnalysis().then(setAnalysis).catch(() => {});
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Investment Portfolio</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Real-time mark-to-market holdings, sector exposures, and deterministic diversification insights
        </p>
      </div>

      {/* Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Current Value</div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '6px' }}>
            ₹{portfolio ? Number(portfolio.current_value).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Total Invested: <span className="mono">₹{portfolio ? Number(portfolio.total_invested).toLocaleString('en-IN') : '0.00'}</span>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Unrealized P&L</div>
          <div className={`mono font-bold ${portfolio && Number(portfolio.total_unrealized_pnl) >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.75rem', marginTop: '6px' }}>
            {portfolio && Number(portfolio.total_unrealized_pnl) >= 0 ? '+' : ''}₹{portfolio ? Number(portfolio.total_unrealized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Return: <span className="mono font-bold">{portfolio ? `${Number(portfolio.total_unrealized_pnl_pct).toFixed(2)}%` : '0.00%'}</span>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Cash Balance</div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '6px', color: 'var(--accent-blue)' }}>
            ₹{portfolio ? Number(portfolio.cash_balance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Available Margin
          </div>
        </div>
      </div>

      {/* Sector Allocation Breakdown */}
      {portfolio?.sector_allocation && (
        <div className="card">
          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PieChart size={18} color="var(--accent-blue)" />
            Sector Weightage Allocation
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
            {Object.entries(portfolio.sector_allocation).map(([sector, pct]: [string, any]) => (
              <div key={sector} style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{sector}</div>
                <div className="mono font-bold" style={{ fontSize: '1.25rem', margin: '4px 0' }}>{Number(pct).toFixed(1)}%</div>
                <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, Number(pct))}%`, height: '100%', background: 'var(--accent-blue)' }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Holdings Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Active Portfolio Holdings ({portfolio?.positions?.length || 0})</h4>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Security</th>
              <th>Sector</th>
              <th style={{ textAlign: 'right' }}>Quantity</th>
              <th style={{ textAlign: 'right' }}>Avg Price (₹)</th>
              <th style={{ textAlign: 'right' }}>Current Price (₹)</th>
              <th style={{ textAlign: 'right' }}>Invested (₹)</th>
              <th style={{ textAlign: 'right' }}>Current Value (₹)</th>
              <th style={{ textAlign: 'right' }}>Unrealized P&L</th>
            </tr>
          </thead>
          <tbody>
            {portfolio?.positions?.map((p: any) => {
              const isProfit = Number(p.unrealized_pnl) >= 0;
              return (
                <tr key={p.id}>
                  <td style={{ fontWeight: 700 }}>{p.symbol}</td>
                  <td><span className="badge badge-blue">{p.sector || 'General'}</span></td>
                  <td style={{ textAlign: 'right' }} className="mono">{p.quantity}</td>
                  <td style={{ textAlign: 'right' }} className="mono">₹{Number(p.average_price).toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }} className="mono font-bold">₹{Number(p.current_price).toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }} className="mono">₹{Number(p.invested_amount).toLocaleString('en-IN')}</td>
                  <td style={{ textAlign: 'right' }} className="mono font-bold">₹{Number(p.current_value).toLocaleString('en-IN')}</td>
                  <td style={{ textAlign: 'right' }} className={isProfit ? 'text-profit mono font-bold' : 'text-loss mono font-bold'}>
                    {isProfit ? '+' : ''}₹{Number(p.unrealized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })} ({isProfit ? '+' : ''}{Number(p.unrealized_pnl_pct).toFixed(2)}%)
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Quantitative Risk & Diversification Intelligence */}
      {analysis && (
        <div className="card card-glow-purple">
          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={18} color="var(--accent-purple)" />
            Deterministic Portfolio Risk Review
          </h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            {analysis.summary}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {analysis.concentration_risks.length > 0 && (
              <div>
                <h5 style={{ fontSize: '0.8rem', color: 'var(--accent-red)', marginBottom: '6px' }}>Concentration Warnings</h5>
                <ul style={{ paddingLeft: '18px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  {analysis.concentration_risks.map((c: string, idx: number) => <li key={idx}>{c}</li>)}
                </ul>
              </div>
            )}
            {analysis.diversification_observations.length > 0 && (
              <div>
                <h5 style={{ fontSize: '0.8rem', color: 'var(--accent-green)', marginBottom: '6px' }}>Diversification Observations</h5>
                <ul style={{ paddingLeft: '18px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  {analysis.diversification_observations.map((d: string, idx: number) => <li key={idx}>{d}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
