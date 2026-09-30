import React from 'react';
import { useMarketStream } from '../context/WebSocketContext';
import { Link } from 'react-router-dom';

const DEFAULT_STOCKS = [
  { symbol: 'NIFTY 50', base: 25850.00, change: 108.20, pct: 0.42 },
  { symbol: 'BANKNIFTY', base: 53400.00, change: 295.40, pct: 0.55 },
  { symbol: 'RELIANCE', base: 2985.50, change: 18.50, pct: 0.62 },
  { symbol: 'TCS', base: 4260.00, change: 32.10, pct: 0.76 },
  { symbol: 'HDFCBANK', base: 1682.25, change: -4.30, pct: -0.25 },
  { symbol: 'INFY', base: 1915.00, change: 12.80, pct: 0.67 },
  { symbol: 'TATAMOTORS', base: 982.50, change: 8.90, pct: 0.91 },
  { symbol: 'ICICIBANK', base: 1248.80, change: 6.40, pct: 0.52 },
];

export const MarketTicker: React.FC = () => {
  const { ticks } = useMarketStream();

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.9)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '6px 16px',
      overflowX: 'auto',
      whiteSpace: 'nowrap',
      display: 'flex',
      gap: '24px',
      alignItems: 'center',
      fontSize: '0.8rem',
      fontWeight: 600
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
        <span className="pulsing-dot green"></span>
        <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>NSE LIVE</span>
      </div>

      {DEFAULT_STOCKS.map((stock) => {
        const liveTick = ticks[stock.symbol];
        const currentPrice = liveTick ? liveTick.price : stock.base;
        const isUp = stock.pct >= 0;

        return (
          <Link
            key={stock.symbol}
            to={`/stock/${encodeURIComponent(stock.symbol)}`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              textDecoration: 'none',
              color: 'var(--text-primary)',
              padding: '2px 8px',
              borderRadius: '4px',
              transition: 'background 0.2s ease'
            }}
          >
            <span style={{ color: 'var(--text-secondary)' }}>{stock.symbol}</span>
            <span className="mono tabular-nums">₹{currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            <span className={isUp ? 'text-profit' : 'text-loss'} style={{ fontSize: '0.75rem' }}>
              {isUp ? '+' : ''}{stock.pct.toFixed(2)}%
            </span>
          </Link>
        );
      })}
    </div>
  );
};
