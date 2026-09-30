import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { Play, TrendingUp, ShieldAlert, Award, Calendar, BarChart2 } from 'lucide-react';

export const Backtests: React.FC = () => {
  const location = useLocation();
  const initialStrat = (location.state as any)?.strategy;
  const { showToast } = useToast();

  const [symbol, setSymbol] = useState('RELIANCE');
  const [daysBack, setDaysBack] = useState('30');
  const [capital, setCapital] = useState('100000');
  const [stopLoss, setStopLoss] = useState('1.5');
  const [target, setTarget] = useState('3.0');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    try {
      const payload = {
        symbol: symbol.toUpperCase(),
        timeframe: '5m',
        days_back: parseInt(daysBack),
        initial_capital: parseFloat(capital),
        stop_loss_pct: parseFloat(stopLoss),
        target_pct: parseFloat(target)
      };
      const data = await ApiClient.runBacktest(payload);
      setResult(data);
      showToast('Backtest simulation completed', 'success');
    } catch (err: any) {
      showToast(err.message || 'Backtest failed', 'error');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Walk-Forward Backtesting Engine</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Historical simulated execution with slippage, brokerage, and risk-adjusted metrics
        </p>
      </div>

      {/* Configuration Card */}
      <form onSubmit={handleRunBacktest} className="card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr)) auto', gap: '12px', alignItems: 'end' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="input"
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Lookback (Days)</label>
          <input
            type="number"
            value={daysBack}
            onChange={(e) => setDaysBack(e.target.value)}
            className="input mono"
            min="5"
            max="365"
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Capital (₹)</label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(e.target.value)}
            className="input mono"
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Stop Loss (%)</label>
          <input
            type="number"
            value={stopLoss}
            onChange={(e) => setStopLoss(e.target.value)}
            className="input mono"
            step="0.1"
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Target (%)</label>
          <input
            type="number"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="input mono"
            step="0.1"
            required
          />
        </div>

        <button type="submit" disabled={isRunning} className="btn btn-primary" style={{ padding: '0.75rem 24px' }}>
          <Play size={16} />
          <span>{isRunning ? 'Simulating...' : 'Run Backtest'}</span>
        </button>
      </form>

      {/* Backtest Results Presentation */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Key Quantitative Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
            <div className="card">
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Net Return</div>
              <div className="mono font-bold" style={{ fontSize: '1.5rem', color: Number(result.total_return) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)', marginTop: '4px' }}>
                {Number(result.total_return) >= 0 ? '+' : ''}{Number(result.total_return).toFixed(2)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CAGR: {Number(result.cagr).toFixed(1)}%</div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Win Rate</div>
              <div className="mono font-bold" style={{ fontSize: '1.5rem', color: 'var(--accent-green)', marginTop: '4px' }}>
                {Number(result.win_rate).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Trades: {result.trade_count}</div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Profit Factor</div>
              <div className="mono font-bold" style={{ fontSize: '1.5rem', color: '#fff', marginTop: '4px' }}>
                {Number(result.profit_factor).toFixed(2)}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Gross Profit / Gross Loss</div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Max Drawdown</div>
              <div className="mono font-bold" style={{ fontSize: '1.5rem', color: 'var(--accent-red)', marginTop: '4px' }}>
                -{Number(result.max_drawdown).toFixed(2)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Peak to Valley Drawdown</div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sharpe Ratio</div>
              <div className="mono font-bold" style={{ fontSize: '1.5rem', color: 'var(--accent-blue)', marginTop: '4px' }}>
                {Number(result.sharpe_ratio).toFixed(2)}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Risk-Free Rate: 6.5%</div>
            </div>
          </div>

          {/* Equity Curve SVG Visualization */}
          <div className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Simulated Equity Curve</h4>
              <span className="badge badge-purple">SIMULATED WALK-FORWARD</span>
            </div>

            {result.equity_curve && result.equity_curve.length > 1 && (
              <div style={{ height: '160px', width: '100%', position: 'relative' }}>
                <svg width="100%" height="100%" viewBox="0 0 800 160" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="eqGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                      <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>
                  {(() => {
                    const equities = result.equity_curve.map((e: any) => Number(e.equity));
                    const maxE = Math.max(...equities);
                    const minE = Math.min(...equities);
                    const rangeE = maxE - minE || 1;
                    const pts = result.equity_curve.map((pt: any, i: number) => {
                      const x = (i / (result.equity_curve.length - 1)) * 800;
                      const y = 150 - ((Number(pt.equity) - minE) / rangeE) * 130;
                      return `${x},${y}`;
                    }).join(' ');

                    return (
                      <>
                        <polygon points={`0,160 ${pts} 800,160`} fill="url(#eqGrad)" />
                        <polyline points={pts} fill="none" stroke="#10b981" strokeWidth="2.5" />
                      </>
                    );
                  })()}
                </svg>
              </div>
            )}
          </div>

          {/* Trade History Table */}
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Simulated Trade Log ({result.trades?.length || 0})</h4>
            </div>

            <table className="data-table">
              <thead>
                <tr>
                  <th>Entry Time</th>
                  <th>Exit Time</th>
                  <th>Side</th>
                  <th style={{ textAlign: 'right' }}>Entry (₹)</th>
                  <th style={{ textAlign: 'right' }}>Exit (₹)</th>
                  <th style={{ textAlign: 'right' }}>Quantity</th>
                  <th style={{ textAlign: 'right' }}>P&L (₹)</th>
                  <th>Exit Reason</th>
                </tr>
              </thead>
              <tbody>
                {result.trades?.map((tr: any, idx: number) => (
                  <tr key={idx}>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{new Date(tr.entry_time).toLocaleDateString()}</td>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{new Date(tr.exit_time).toLocaleDateString()}</td>
                    <td><span className="badge badge-green">{tr.side}</span></td>
                    <td style={{ textAlign: 'right' }} className="mono">₹{Number(tr.entry_price).toFixed(2)}</td>
                    <td style={{ textAlign: 'right' }} className="mono">₹{Number(tr.exit_price).toFixed(2)}</td>
                    <td style={{ textAlign: 'right' }} className="mono">{tr.quantity}</td>
                    <td style={{ textAlign: 'right' }} className={Number(tr.pnl) >= 0 ? 'text-profit mono font-bold' : 'text-loss mono font-bold'}>
                      {Number(tr.pnl) >= 0 ? '+' : ''}₹{Number(tr.pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td>
                      <span className={tr.exit_reason === 'TARGET' ? 'badge badge-green' : tr.exit_reason === 'STOP_LOSS' ? 'badge badge-red' : 'badge badge-amber'}>
                        {tr.exit_reason}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
