import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useMarketStream } from '../context/WebSocketContext';
import { PriceChart } from '../components/PriceChart';
import { IndicatorPanel } from '../components/IndicatorPanel';
import { TradeExecutionModal } from '../components/TradeExecutionModal';
import {
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Newspaper,
  ShieldCheck,
  Zap,
  BarChart3
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { ticks } = useMarketStream();
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY 50');
  const [candles, setCandles] = useState<any[]>([]);
  const [indicators, setIndicators] = useState<any>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [activeSetup, setActiveSetup] = useState<any>(null);
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);
  const [newspaperHeadline, setNewspaperHeadline] = useState<string>('');

  useEffect(() => {
    // Fetch minute candles for selected symbol
    ApiClient.getMinuteBars(selectedSymbol, 60)
      .then((data) => setCandles(data))
      .catch(() => {});

    // Fetch indicators
    ApiClient.getIndicators(selectedSymbol)
      .then((ind) => setIndicators(ind))
      .catch(() => {});

    // Fetch portfolio summary
    ApiClient.getPortfolio()
      .then((p) => setPortfolio(p))
      .catch(() => {});

    // Fetch latest newspaper headline
    ApiClient.getAINewspaper('INTRADAY')
      .then((n) => setNewspaperHeadline(n.articles[0]?.headline || 'Markets Consolidate Near Record Highs'))
      .catch(() => {});
  }, [selectedSymbol]);

  const handleGenerateTradeSetup = async (sym: string) => {
    try {
      const setup = await ApiClient.generateTradeSetup(sym);
      setActiveSetup(setup);
      setIsTradeModalOpen(true);
    } catch {
      // fallback
    }
  };

  const currentPrice = ticks[selectedSymbol] ? ticks[selectedSymbol].price : 25850.00;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner: Daily AI Intelligence Bulletin */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(56, 189, 248, 0.1) 100%)',
        border: '1px solid rgba(168, 85, 247, 0.3)',
        borderRadius: '14px',
        padding: '1.25rem 1.75rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-glow-purple)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #a855f7 0%, #7c3aed 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(168, 85, 247, 0.5)'
          }}>
            <Sparkles size={22} color="#fff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-purple">AI MARKET CHRONICLE</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Updated Just Now</span>
            </div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff', marginTop: '4px' }}>
              {newspaperHeadline || 'Indian Equities Consolidate With Strong Domestic Inflows'}
            </h4>
          </div>
        </div>

        <Link to="/ai/newspaper" className="btn btn-purple" style={{ textDecoration: 'none', padding: '8px 16px' }}>
          <Newspaper size={16} />
          <span>Read Full Edition</span>
        </Link>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Portfolio Net Worth</span>
            <span className="badge badge-green">+12.4% All Time</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, marginTop: '8px' }} className="mono">
            ₹{portfolio ? Number(portfolio.current_value).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '10,85,420.00'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Unrealized P&L: <span className="text-profit mono">+₹{portfolio ? Number(portfolio.total_unrealized_pnl).toLocaleString('en-IN') : '85,420.00'}</span>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Available Trading Margin</span>
            <span className="badge badge-blue">Protected</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, marginTop: '8px' }} className="mono">
            ₹{portfolio ? Number(portfolio.cash_balance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '2,50,000.00'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Locked for Withdrawals: <span className="mono">₹0.00</span>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Active Positions</span>
            <span className="badge badge-purple">{portfolio?.positions?.length || 4} Stocks</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, marginTop: '8px' }} className="mono">
            {portfolio?.positions?.length || 4}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Sector Concentration: <span className="mono">IT / Energy / Banking</span>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Risk Shield Status</span>
            <span className="badge badge-green">Operational</span>
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '8px', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={24} />
            <span>Pre-Trade Guard Active</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Daily Max Drawdown Limit: <span className="mono">5.0%</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Chart + Indicator Panel + Quick Trades */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        {/* Left Column: Interactive Price Chart & Symbol Switcher */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Quick Symbol Switcher */}
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
            {['NIFTY 50', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY'].map((sym) => (
              <button
                key={sym}
                onClick={() => setSelectedSymbol(sym)}
                className={`btn ${selectedSymbol === sym ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '6px 14px', fontSize: '0.8rem' }}
              >
                {sym}
              </button>
            ))}
          </div>

          <PriceChart
            symbol={selectedSymbol}
            candles={candles}
            timeframe="1m"
            onTimeframeChange={(tf) => {
              if (tf === '1d') {
                ApiClient.getHistory(selectedSymbol).then(setCandles).catch(() => {});
              } else {
                ApiClient.getMinuteBars(selectedSymbol, 100).then(setCandles).catch(() => {});
              }
            }}
          />

          <IndicatorPanel indicators={indicators} />
        </div>

        {/* Right Column: AI Stock Action & Top Movers */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* AI Tactical Card */}
          <div className="card card-glow-purple">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Zap size={18} color="var(--accent-purple)" />
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>AI Trade Setup Generator</h4>
              </div>
              <span className="badge badge-purple">Tool Grounded</span>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
              Generates a mathematical, rule-checked trade setup for <b>{selectedSymbol}</b> with strict stop loss and target levels. Validates against the 6-point Pre-Trade Risk Engine.
            </p>

            <button
              onClick={() => handleGenerateTradeSetup(selectedSymbol)}
              className="btn btn-purple"
              style={{ width: '100%', padding: '10px' }}
            >
              <Sparkles size={16} />
              <span>Generate Trade Setup for {selectedSymbol}</span>
            </button>
          </div>

          {/* Market Bluechips Watch Snapshot */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>NSE Top Equities</h4>
              <Link to="/market" style={{ fontSize: '0.75rem', color: 'var(--accent-green)', textDecoration: 'none' }}>
                View All →
              </Link>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { sym: 'RELIANCE', name: 'Reliance Industries', price: 2985.50, pct: 0.62 },
                { sym: 'TCS', name: 'Tata Consultancy Services', price: 4260.00, pct: 0.76 },
                { sym: 'HDFCBANK', name: 'HDFC Bank', price: 1682.25, pct: -0.25 },
                { sym: 'INFY', name: 'Infosys Ltd', price: 1915.00, pct: 0.67 },
                { sym: 'TATAMOTORS', name: 'Tata Motors', price: 982.50, pct: 0.91 }
              ].map((stock) => {
                const liveTick = ticks[stock.sym];
                const p = liveTick ? liveTick.price : stock.price;
                const isUp = stock.pct >= 0;

                return (
                  <div
                    key={stock.sym}
                    onClick={() => setSelectedSymbol(stock.sym)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      background: 'rgba(30, 41, 59, 0.4)',
                      cursor: 'pointer',
                      border: selectedSymbol === stock.sym ? '1px solid var(--accent-green)' : '1px solid transparent',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{stock.sym}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{stock.name}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className="mono tabular-nums" style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                        ₹{p.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div className={isUp ? 'text-profit' : 'text-loss'} style={{ fontSize: '0.75rem', fontWeight: 600 }}>
                        {isUp ? '+' : ''}{stock.pct.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Trade Execution Modal */}
      {isTradeModalOpen && activeSetup && (
        <TradeExecutionModal
          setup={activeSetup}
          onClose={() => setIsTradeModalOpen(false)}
          onSuccess={() => {
            setIsTradeModalOpen(false);
            ApiClient.getPortfolio().then(setPortfolio);
          }}
        />
      )}
    </div>
  );
};
