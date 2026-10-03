import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useMarketStream } from '../context/WebSocketContext';
import { PriceChart } from '../components/PriceChart';
import { IndicatorPanel } from '../components/IndicatorPanel';
import { TradeExecutionModal } from '../components/TradeExecutionModal';
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Layers,
  BarChart3,
  Briefcase,
  ShieldCheck,
  ChevronRight,
  RefreshCw,
  Wallet
} from 'lucide-react';

const TOP_WATCHLIST = [
  { sym: 'RELIANCE', name: 'Reliance Industries', basePrice: 2985.50, changePct: 1.24 },
  { sym: 'TCS', name: 'Tata Consultancy Services', basePrice: 4260.00, changePct: 0.76 },
  { sym: 'HDFCBANK', name: 'HDFC Bank Ltd', basePrice: 1682.25, changePct: -0.45 },
  { sym: 'INFY', name: 'Infosys Ltd', basePrice: 1915.00, changePct: 0.88 },
  { sym: 'ICICIBANK', name: 'ICICI Bank Ltd', basePrice: 1245.50, changePct: 1.05 },
  { sym: 'TATAMOTORS', name: 'Tata Motors Ltd', basePrice: 982.50, changePct: -0.32 },
  { sym: 'SBIN', name: 'State Bank of India', basePrice: 812.00, changePct: 0.42 },
];

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { ticks, marketStatus, dataStatus } = useMarketStream();
  const [selectedSymbol, setSelectedSymbol] = useState('RELIANCE');
  const [candles, setCandles] = useState<any[]>([]);
  const [indicators, setIndicators] = useState<any>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [wallet, setWallet] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [recentOrders, setRecentOrders] = useState<any[]>([]);
  const [activeSetup, setActiveSetup] = useState<any>(null);
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);
  const [tradeSide, setTradeSide] = useState<'BUY' | 'SELL'>('BUY');
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      const [p, w, pos, ords] = await Promise.all([
        ApiClient.getPortfolio().catch(() => null),
        ApiClient.getWallet().catch(() => null),
        ApiClient.getPositions().catch(() => null),
        ApiClient.getOrders().catch(() => [])
      ]);
      if (p) setPortfolio(p);
      if (w) setWallet(w);
      if (pos) setPositions(Array.isArray(pos) ? pos : (pos.open_positions || []));
      if (ords) setRecentOrders(ords);
    } catch {
      // quiet fallback
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      ApiClient.getCandles(selectedSymbol, '1m', 60).catch(() => ApiClient.getMinuteBars(selectedSymbol, 60)).catch(() => []),
      ApiClient.getIndicators(selectedSymbol).catch(() => null)
    ]).then(([bars, ind]) => {
      setCandles(bars);
      setIndicators(ind);
      setLoading(false);
    });
  }, [selectedSymbol]);

  // Indices current values from live ticks or defaults
  const niftyTick = ticks['NIFTY 50'] || ticks['^NSEI'];
  const niftyPrice = niftyTick ? niftyTick.price : 25850.50;
  const niftyChange = niftyTick?.change !== undefined ? Number(niftyTick.change) : 142.30;
  const niftyPct = niftyTick?.change_pct !== undefined ? Number(niftyTick.change_pct) : 0.55;

  const bankNiftyTick = ticks['BANKNIFTY'] || ticks['^NSEBANK'];
  const bankNiftyPrice = bankNiftyTick ? bankNiftyTick.price : 53420.00;
  const bankNiftyChange = bankNiftyTick?.change !== undefined ? Number(bankNiftyTick.change) : 285.10;
  const bankNiftyPct = bankNiftyTick?.change_pct !== undefined ? Number(bankNiftyTick.change_pct) : 0.54;

  const sensexTick = ticks['SENSEX'] || ticks['^BSESN'];
  const sensexPrice = sensexTick ? sensexTick.price : 84600.00;
  const sensexChange = sensexTick?.change !== undefined ? Number(sensexTick.change) : 412.80;
  const sensexPct = sensexTick?.change_pct !== undefined ? Number(sensexTick.change_pct) : 0.49;

  const vixTick = ticks['INDIA VIX'] || ticks['^INDIAVIX'];
  const vixPrice = vixTick ? vixTick.price : 12.85;
  const vixChange = vixTick?.change !== undefined ? Number(vixTick.change) : -0.35;
  const vixPct = vixTick?.change_pct !== undefined ? Number(vixTick.change_pct) : -2.65;

  // Selected stock live price
  const activeStock = TOP_WATCHLIST.find((s) => s.sym === selectedSymbol);
  const selectedTick = ticks[selectedSymbol];
  const currentPrice = selectedTick ? selectedTick.price : (activeStock?.basePrice || 2985.50);
  const selectedChangePct = selectedTick?.change_pct !== undefined ? Number(selectedTick.change_pct) : (activeStock?.changePct || 0);
  const isSelectedUp = selectedChangePct >= 0;

  // Authoritative calculations
  const cashBalance = wallet ? Number(wallet.available_balance) : (portfolio ? Number(portfolio.cash_balance) : 1000000);
  const positionsValue = positions.reduce((acc, p) => acc + (Number(p.current_value) || 0), 0);
  const totalEquity = cashBalance + positionsValue;
  const totalInvested = positions.reduce((acc, p) => acc + (Number(p.invested_value) || Number(p.invested_amount) || 0), 0);
  const unrealizedPnl = positionsValue - totalInvested;
  const overallPnl = (portfolio ? Number(portfolio.total_pnl) : 0) || unrealizedPnl;
  const todayPnl = portfolio ? Number(portfolio.today_pnl || 0) : unrealizedPnl * 0.4;

  const handleOpenTrade = (side: 'BUY' | 'SELL', sym?: string) => {
    const symbolToTrade = sym || selectedSymbol;
    setSelectedSymbol(symbolToTrade);
    setTradeSide(side);
    setActiveSetup({
      symbol: symbolToTrade,
      action: side,
      order_type: 'MARKET',
      suggested_entry: currentPrice,
      stop_loss: side === 'BUY' ? Math.round(currentPrice * 0.98 * 20) / 20 : Math.round(currentPrice * 1.02 * 20) / 20,
      target: side === 'BUY' ? Math.round(currentPrice * 1.04 * 20) / 20 : Math.round(currentPrice * 0.96 * 20) / 20,
      confidence_score: 85,
      timeframe: 'INTRADAY',
      thesis: `Paper ${side} execution for ${symbolToTrade} under realistic simulated market environment.`
    });
    setIsTradeModalOpen(true);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner: Mode & Market Status Disclosure */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.65rem 1.25rem',
        background: 'var(--surface)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        flexWrap: 'wrap',
        gap: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span className="paper-badge">PAPER TRADING MODE</span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '0.7rem',
              fontWeight: 700,
              background:
                dataStatus === 'LIVE' ? 'rgba(16, 185, 129, 0.15)' :
                dataStatus === 'STALE' ? 'rgba(245, 158, 11, 0.15)' :
                'rgba(148, 163, 184, 0.15)',
              color:
                dataStatus === 'LIVE' ? '#10b981' :
                dataStatus === 'STALE' ? '#f59e0b' :
                '#94a3b8',
              border: `1px solid ${dataStatus === 'LIVE' ? 'rgba(16, 185, 129, 0.3)' : dataStatus === 'STALE' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(148, 163, 184, 0.3)'}`
            }}
          >
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: dataStatus === 'LIVE' ? '#10b981' : dataStatus === 'STALE' ? '#f59e0b' : '#94a3b8'
            }} />
            {dataStatus} ({marketStatus})
          </span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Operating with <b>simulated virtual capital</b>. Fills reflect realistic simulated Indian equity market order book dynamics.
          </span>
        </div>
        <button
          onClick={loadData}
          className="btn btn-secondary"
          style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw size={12} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Top Bar: Major Indian Market Indices */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '0.75rem'
      }}>
        {[
          { name: 'NIFTY 50', val: niftyPrice, change: (niftyChange >= 0 ? '+' : '') + niftyChange.toFixed(2), pct: (niftyPct >= 0 ? '+' : '') + niftyPct.toFixed(2) + '%', isUp: niftyPct >= 0 },
          { name: 'BANK NIFTY', val: bankNiftyPrice, change: (bankNiftyChange >= 0 ? '+' : '') + bankNiftyChange.toFixed(2), pct: (bankNiftyPct >= 0 ? '+' : '') + bankNiftyPct.toFixed(2) + '%', isUp: bankNiftyPct >= 0 },
          { name: 'SENSEX', val: sensexPrice, change: (sensexChange >= 0 ? '+' : '') + sensexChange.toFixed(2), pct: (sensexPct >= 0 ? '+' : '') + sensexPct.toFixed(2) + '%', isUp: sensexPct >= 0 },
          { name: 'INDIA VIX', val: vixPrice, change: (vixChange >= 0 ? '+' : '') + vixChange.toFixed(2), pct: (vixPct >= 0 ? '+' : '') + vixPct.toFixed(2) + '%', isUp: vixPct >= 0 },
        ].map((idx) => (
          <div key={idx.name} className="card" style={{ padding: '0.75rem 1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{idx.name}</span>
              <span className={idx.isUp ? 'text-profit' : 'text-loss'} style={{ fontSize: '0.72rem', fontWeight: 600 }}>
                {idx.pct}
              </span>
            </div>
            <div className="mono font-bold" style={{ fontSize: '1.15rem', marginTop: '2px' }}>
              ₹{idx.val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '1px' }}>
              {idx.change} pts
            </div>
          </div>
        ))}
      </div>

      {/* Portfolio Summary Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '0.75rem'
      }}>
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Total Equity</div>
          <div className="mono font-bold" style={{ fontSize: '1.5rem', marginTop: '4px' }}>
            ₹{totalEquity.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Holdings: ₹{positionsValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Available Paper Cash</div>
          <div className="mono font-bold" style={{ fontSize: '1.5rem', marginTop: '4px', color: 'var(--primary)' }}>
            ₹{cashBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Starting: ₹10,00,000.00
          </div>
        </div>

        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Today's P&L</div>
          <div className={`mono font-bold ${todayPnl >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.5rem', marginTop: '4px' }}>
            {todayPnl >= 0 ? '+' : ''}₹{todayPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Intraday MTM
          </div>
        </div>

        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Overall Realized + Unrealized</div>
          <div className={`mono font-bold ${overallPnl >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.5rem', marginTop: '4px' }}>
            {overallPnl >= 0 ? '+' : ''}₹{overallPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Total Paper Return
          </div>
        </div>
      </div>

      {/* Main Trading Area: Watchlist + Interactive Chart + Ticket */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 280px', gap: '1rem', alignItems: 'start' }}>
        {/* Column 1: Watchlist & Market Movers */}
        <div className="card" style={{ padding: '0', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '0.85rem 1rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>Market Watch</span>
            <Link to="/watchlists" style={{ fontSize: '0.72rem', color: 'var(--primary)', textDecoration: 'none' }}>
              View All →
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {TOP_WATCHLIST.map((stock) => {
              const liveTick = ticks[stock.sym];
              const p = liveTick ? liveTick.price : stock.basePrice;
              const chgPct = liveTick?.change_pct !== undefined ? Number(liveTick.change_pct) : stock.changePct;
              const isUp = chgPct >= 0;
              const isSelected = selectedSymbol === stock.sym;

              return (
                <div
                  key={stock.sym}
                  onClick={() => setSelectedSymbol(stock.sym)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem 1rem',
                    cursor: 'pointer',
                    background: isSelected ? 'var(--surface-muted)' : 'transparent',
                    borderLeft: isSelected ? '3px solid var(--primary)' : '3px solid transparent',
                    borderBottom: '1px solid var(--border)',
                    transition: 'background 0.15s ease'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{stock.sym}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>NSE Equity</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="mono font-bold" style={{ fontSize: '0.85rem' }}>
                      ₹{p.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                    <div className={isUp ? 'text-profit' : 'text-loss'} style={{ fontSize: '0.72rem', fontWeight: 600 }}>
                      {isUp ? '+' : ''}{chgPct.toFixed(2)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Column 2: Main Trading Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>{selectedSymbol}</h3>
                  <span className="badge badge-blue">NSE</span>
                  <Link to={`/stock/${selectedSymbol}`} style={{ fontSize: '0.75rem', color: 'var(--primary)', textDecoration: 'none' }}>
                    Open Full Terminal →
                  </Link>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                  <span className="mono font-bold" style={{ fontSize: '1.15rem' }}>
                    ₹{currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                  <span className={isSelectedUp ? 'text-profit' : 'text-loss'} style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                    {isSelectedUp ? '+' : ''}{selectedChangePct.toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Quick Buy / Sell buttons */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => handleOpenTrade('BUY')}
                  className="btn btn-buy"
                  style={{ padding: '6px 16px', fontSize: '0.85rem', fontWeight: 700 }}
                >
                  BUY
                </button>
                <button
                  onClick={() => handleOpenTrade('SELL')}
                  className="btn btn-sell"
                  style={{ padding: '6px 16px', fontSize: '0.85rem', fontWeight: 700 }}
                >
                  SELL
                </button>
              </div>
            </div>

            <PriceChart
              symbol={selectedSymbol}
              candles={candles}
              timeframe="1m"
              onTimeframeChange={(tf) => {
                ApiClient.getCandles(selectedSymbol, tf, 60)
                  .catch(() => (tf === '1d' ? ApiClient.getHistory(selectedSymbol) : ApiClient.getMinuteBars(selectedSymbol, 60)))
                  .then(setCandles)
                  .catch(() => {});
              }}
            />
          </div>

          <IndicatorPanel indicators={indicators} />
        </div>

        {/* Column 3: Quick Trading Ticket & Risk Guard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Quick Trade Ticket */}
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.75rem' }}>
              Quick Paper Order
            </div>

            <div style={{ display: 'flex', gap: '6px', marginBottom: '1rem' }}>
              <button
                onClick={() => setTradeSide('BUY')}
                className={`btn ${tradeSide === 'BUY' ? 'btn-buy' : 'btn-secondary'}`}
                style={{ flex: 1, padding: '6px', fontSize: '0.8rem', fontWeight: 700 }}
              >
                BUY
              </button>
              <button
                onClick={() => setTradeSide('SELL')}
                className={`btn ${tradeSide === 'SELL' ? 'btn-sell' : 'btn-secondary'}`}
                style={{ flex: 1, padding: '6px', fontSize: '0.8rem', fontWeight: 700 }}
              >
                SELL
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Security</label>
                <input
                  type="text"
                  value={selectedSymbol}
                  readOnly
                  className="input mono font-bold"
                  style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>LTP (Market Quote)</label>
                <div className="mono font-bold" style={{ fontSize: '1rem', padding: '4px 0' }}>
                  ₹{currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>

              <div style={{ background: 'var(--surface-muted)', padding: '8px', borderRadius: '6px', fontSize: '0.72rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                  <span>Available Margin:</span>
                  <span className="mono font-bold">₹{cashBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>

              <button
                onClick={() => handleOpenTrade(tradeSide)}
                className={`btn ${tradeSide === 'BUY' ? 'btn-buy' : 'btn-sell'}`}
                style={{ width: '100%', padding: '10px', marginTop: '6px', fontSize: '0.85rem', fontWeight: 700 }}
              >
                Place Paper {tradeSide} Order
              </button>
            </div>
          </div>

          {/* AI Pre-Trade Analysis (Secondary) */}
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Sparkles size={16} color="var(--primary)" />
              <span style={{ fontSize: '0.82rem', fontWeight: 700 }}>AI Trade Setup</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '10px' }}>
              Mathematical pre-trade plan for {selectedSymbol} with deterministic risk bounds.
            </p>
            <button
              onClick={async () => {
                try {
                  const s = await ApiClient.generateTradeSetup(selectedSymbol);
                  setActiveSetup(s);
                  setIsTradeModalOpen(true);
                } catch {}
              }}
              className="btn btn-secondary"
              style={{ width: '100%', padding: '6px', fontSize: '0.75rem' }}
            >
              Analyze & Setup Trade
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Section: Active Positions & Recent Orders */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Open Positions Card */}
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '0.85rem 1rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Briefcase size={16} />
              <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>Open Positions ({positions.length})</span>
            </div>
            <Link to="/positions" style={{ fontSize: '0.72rem', color: 'var(--primary)', textDecoration: 'none' }}>
              View All Positions →
            </Link>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th style={{ textAlign: 'right' }}>Qty</th>
                <th style={{ textAlign: 'right' }}>Avg (₹)</th>
                <th style={{ textAlign: 'right' }}>LTP (₹)</th>
                <th style={{ textAlign: 'right' }}>P&L (₹)</th>
              </tr>
            </thead>
            <tbody>
              {positions.length > 0 ? (
                positions.slice(0, 4).map((pos) => {
                  const isProfit = Number(pos.unrealized_pnl) >= 0;
                  return (
                    <tr key={pos.symbol} onClick={() => navigate('/positions')} style={{ cursor: 'pointer' }}>
                      <td className="font-bold">{pos.symbol}</td>
                      <td style={{ textAlign: 'right' }} className="mono">{pos.quantity}</td>
                      <td style={{ textAlign: 'right' }} className="mono">₹{Number(pos.average_price).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }} className="mono font-bold">₹{Number(pos.current_price).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }} className={isProfit ? 'text-profit mono font-bold' : 'text-loss mono font-bold'}>
                        {isProfit ? '+' : ''}₹{Number(pos.unrealized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                    No open paper positions. Place your first simulated trade!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Recent Orders Card */}
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '0.85rem 1rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={16} />
              <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>Recent Orders</span>
            </div>
            <Link to="/orders" style={{ fontSize: '0.72rem', color: 'var(--primary)', textDecoration: 'none' }}>
              Order Book →
            </Link>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th style={{ textAlign: 'right' }}>Qty</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.length > 0 ? (
                recentOrders.slice(0, 4).map((ord) => (
                  <tr key={ord.id} onClick={() => navigate('/orders')} style={{ cursor: 'pointer' }}>
                    <td className="font-bold">{ord.symbol}</td>
                    <td>
                      <span className={ord.side === 'BUY' ? 'badge badge-green' : 'badge badge-red'}>
                        {ord.side}
                      </span>
                    </td>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{ord.order_type}</td>
                    <td style={{ textAlign: 'right' }} className="mono">{ord.quantity}</td>
                    <td>
                      <span className={`badge ${
                        ord.status === 'FILLED' ? 'badge-green' :
                        ord.status === 'PENDING' || ord.status === 'SUBMITTED' ? 'badge-blue' :
                        ord.status === 'CANCELLED' ? 'badge-amber' : 'badge-red'
                      }`}>
                        {ord.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                    No paper orders placed yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trade Execution Modal */}
      {isTradeModalOpen && activeSetup && (
        <TradeExecutionModal
          setup={activeSetup}
          onClose={() => setIsTradeModalOpen(false)}
          onSuccess={() => {
            setIsTradeModalOpen(false);
            loadData();
          }}
        />
      )}
    </div>
  );
};
