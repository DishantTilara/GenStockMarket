import React from 'react';
import { TrendingUp, Activity, BarChart2, ShieldAlert } from 'lucide-react';

interface IndicatorPanelProps {
  symbol?: string;
  indicators: any;
}

export const IndicatorPanel: React.FC<IndicatorPanelProps> = ({ indicators }) => {
  if (!indicators) return null;

  const rsi = indicators.rsi_14 || 50;
  const trend = indicators.trend || 'NEUTRAL';
  const vwap = indicators.vwap || 0;
  const support = indicators.support || 0;
  const resistance = indicators.resistance || 0;

  const getTrendBadge = (t: string) => {
    if (t.includes('BULLISH')) return <span className="badge badge-green">{t}</span>;
    if (t.includes('BEARISH')) return <span className="badge badge-red">{t}</span>;
    return <span className="badge badge-amber">{t}</span>;
  };

  const getRSIBadge = (val: number) => {
    if (val >= 70) return <span className="badge badge-red">Overbought ({val.toFixed(1)})</span>;
    if (val <= 35) return <span className="badge badge-green">Oversold ({val.toFixed(1)})</span>;
    return <span className="badge badge-blue">Neutral ({val.toFixed(1)})</span>;
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h4 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} color="var(--accent-green)" />
          Technical Indicator Suite
        </h4>
        <div>{getTrendBadge(trend)}</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '14px' }}>
        {/* RSI */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>RSI (14)</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '4px 0' }} className="mono">{rsi.toFixed(1)}</div>
          <div>{getRSIBadge(rsi)}</div>
        </div>

        {/* EMA 20 & 50 */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>20 EMA / 50 EMA</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, margin: '4px 0' }} className="mono">
            ₹{Number(indicators.ema_20 || 0).toFixed(1)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }} className="mono">
            50: ₹{Number(indicators.ema_50 || 0).toFixed(1)}
          </div>
        </div>

        {/* VWAP */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Intraday VWAP</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '4px 0', color: 'var(--accent-blue)' }} className="mono">
            ₹{Number(vwap).toFixed(2)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Volume-weighted</div>
        </div>

        {/* Support & Resistance */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Support / Resistance</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-green)', margin: '2px 0' }} className="mono">
            S: ₹{Number(support).toFixed(2)}
          </div>
          <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-red)' }} className="mono">
            R: ₹{Number(resistance).toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
};
