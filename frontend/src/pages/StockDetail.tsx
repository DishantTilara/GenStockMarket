import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useWebSocket } from '../context/WebSocketContext';
import { useToast } from '../context/ToastContext';
import { PriceChart } from '../components/PriceChart';
import { IndicatorPanel } from '../components/IndicatorPanel';
import { TradeExecutionModal } from '../components/TradeExecutionModal';
import {
  Star,
  RefreshCw,
  Search,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  Lock,
  Layers,
  BarChart2,
  FileText,
  ShieldCheck,
  TrendingUp,
  Clock
} from 'lucide-react';

const POPULAR_SYMBOLS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'BHARTIARTL', 'SBIN', 'ITC', 'LT', 'TATAMOTORS'];

export const StockDetail: React.FC = () => {
  const { symbol: routeSymbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const sym = (routeSymbol || 'RELIANCE').toUpperCase();

  const [quote, setQuote] = useState<any>(null);
  const [candles, setCandles] = useState<any[]>([]);
  const [indicators, setIndicators] = useState<any>(null);
  const [activeTimeframe, setActiveTimeframe] = useState('1m');
  const [wallet, setWallet] = useState<any>(null);
  const [ownedQty, setOwnedQty] = useState(0);

  // In-Workspace Order Form
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [quantity, setQuantity] = useState(10);
  const [limitPrice, setLimitPrice] = useState<number>(0);
  const [stopLoss, setStopLoss] = useState<number | undefined>();
  const [target, setTarget] = useState<number | undefined>();
  const [orderSubmitting, setOrderSubmitting] = useState(false);
  const [riskValidating, setRiskValidating] = useState(false);

  // Workspace Tabs
  const [activeBottomTab, setActiveBottomTab] = useState<'INDICATORS' | 'SETUP' | 'FUNDAMENTALS' | 'OPTIONS'>('INDICATORS');
  const [tradeSetup, setTradeSetup] = useState<any>(null);
  const [fundamentals, setFundamentals] = useState<any>(null);
  const [isLoadingFundamentals, setIsLoadingFundamentals] = useState(false);
  const [optionChain, setOptionChain] = useState<any>(null);
  const [selectedExpiry, setSelectedExpiry] = useState<string>('');
  const [isLoadingOptions, setIsLoadingOptions] = useState(false);
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);

  const { marketTicks, marketStatus, dataStatus } = useWebSocket();
  const { showToast } = useToast();

  const loadStockData = async () => {
    try {
      const [quoteData, barsData, indData, walletData, posData, fundData] = await Promise.all([
        ApiClient.getQuote(sym).catch(() => null),
        ApiClient.getCandles(sym, activeTimeframe, 120).catch(() => ApiClient.getMinuteBars(sym, 120)),
        ApiClient.getIndicators(sym, activeTimeframe).catch(() => null),
        ApiClient.getWallet().catch(() => null),
        ApiClient.getPositions().catch(() => null),
        ApiClient.getFundamentals(sym).catch(() => null)
      ]);
      if (quoteData) {
        setQuote(quoteData);
        const ltp = Number(quoteData.price);
        if (!limitPrice) setLimitPrice(ltp);
      }
      if (barsData) setCandles(barsData);
      if (indData) setIndicators(indData);
      if (walletData) setWallet(walletData);
      if (fundData) setFundamentals(fundData);

      if (posData) {
        const holding = posData.open_positions?.find((p: any) => p.symbol === sym);
        setOwnedQty(holding ? holding.quantity : 0);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const fetchOptions = async (expiry?: string) => {
    try {
      setIsLoadingOptions(true);
      const data = await ApiClient.getOptionChain(sym, expiry);
      setOptionChain(data);
      if (!selectedExpiry && data.selected_expiry) {
        setSelectedExpiry(data.selected_expiry);
      }
    } catch (err) {
      console.error('Failed to load option chain:', err);
    } finally {
      setIsLoadingOptions(false);
    }
  };

  useEffect(() => {
    loadStockData();
  }, [sym, activeTimeframe]);

  useEffect(() => {
    if (activeBottomTab === 'OPTIONS') {
      fetchOptions(selectedExpiry || undefined);
    }
  }, [activeBottomTab, selectedExpiry, sym]);

  // Live WebSocket Tick Update
  const liveTick = marketTicks[sym];
  const currentPrice = liveTick ? liveTick.price : quote ? Number(quote.price) : 2985.50;
  const changeVal = liveTick?.change !== undefined ? Number(liveTick.change) : quote ? Number(quote.change || 0) : 0;
  const changePct = liveTick?.change_pct !== undefined ? Number(liveTick.change_pct) : quote ? Number(quote.change_pct || 0) : 0.0;
  const openPrice = liveTick?.open ?? (quote ? Number(quote.open) : null);
  const highPrice = liveTick?.high ?? (quote ? Number(quote.high) : null);
  const lowPrice = liveTick?.low ?? (quote ? Number(quote.low) : null);
  const prevClose = liveTick?.previous_close ?? (quote ? Number(quote.previous_close) : null);
  const volume = liveTick?.volume ?? (quote ? Number(quote.volume) : null);
  const quoteTimestamp = liveTick?.timestamp ?? quote?.timestamp;
  const freshness = liveTick?.freshness ?? quote?.freshness ?? dataStatus;
  const isUp = changePct >= 0;

  const effectivePrice = orderType === 'MARKET' ? currentPrice : (limitPrice || currentPrice);
  const orderTurnover = effectivePrice * quantity;
  const estimatedCharges = Math.max(20, orderTurnover * 0.0012);
  const totalCost = orderTurnover + estimatedCharges;
  const availableCash = wallet ? Number(wallet.available_balance) : 1000000;

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setOrderSubmitting(true);
      const order = await ApiClient.createOrder({
        symbol: sym,
        side: orderSide,
        order_type: orderType,
        quantity,
        price: orderType === 'LIMIT' ? limitPrice : undefined,
        stop_loss: stopLoss,
        target_price: target
      });

      showToast(`Paper order placed: ${order.side} ${order.quantity} ${order.symbol} (${order.status})`, 'success');
      // Refresh wallet & positions
      loadStockData();
    } catch (err: any) {
      showToast(err.message || 'Order execution failed', 'error');
    } finally {
      setOrderSubmitting(false);
    }
  };

  const handleFetchTradeSetup = async () => {
    try {
      setRiskValidating(true);
      const setup = await ApiClient.generateTradeSetup(sym);
      setTradeSetup(setup);
      if (setup.side) setOrderSide(setup.side as 'BUY' | 'SELL');
      if (setup.quantity) setQuantity(setup.quantity);
      if (setup.stop_loss) setStopLoss(Number(setup.stop_loss));
      if (setup.target_price) setTarget(Number(setup.target_price));
      showToast(`Generated automated setup for ${sym}`, 'info');
    } catch (err: any) {
      showToast(err.message || 'Setup generation failed', 'error');
    } finally {
      setRiskValidating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Symbol Navigation Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', background: 'var(--surface)', padding: '0.75rem 1rem', borderRadius: '10px', border: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>QUICK SWITCH:</span>
          {POPULAR_SYMBOLS.slice(0, 7).map(s => (
            <button
              key={s}
              onClick={() => navigate(`/stock/${s}`)}
              style={{
                background: s === sym ? 'var(--primary)' : 'var(--surface-muted)',
                color: s === sym ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '5px',
                padding: '0.25rem 0.6rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {s}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="paper-badge">PAPER TRADING WORKSPACE</span>
        </div>
      </div>

      {/* Main Stock Header */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0 }}>{sym}</h1>
              <span className="badge badge-blue">NSE</span>
              <span className="badge" style={{ background: 'var(--surface-muted)', color: 'var(--text-secondary)' }}>
                {quote?.sector || 'EQUITY'}
              </span>
              {quote?.provider_symbol && (
                <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  [{quote.provider_symbol}]
                </span>
              )}
              {/* Freshness Badge */}
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
                    freshness === 'LIVE' ? 'rgba(16, 185, 129, 0.15)' :
                    freshness === 'STALE' ? 'rgba(245, 158, 11, 0.15)' :
                    'rgba(148, 163, 184, 0.15)',
                  color:
                    freshness === 'LIVE' ? '#10b981' :
                    freshness === 'STALE' ? '#f59e0b' :
                    '#94a3b8',
                  border: `1px solid ${freshness === 'LIVE' ? 'rgba(16, 185, 129, 0.3)' : freshness === 'STALE' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(148, 163, 184, 0.3)'}`
                }}
              >
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: freshness === 'LIVE' ? '#10b981' : freshness === 'STALE' ? '#f59e0b' : '#94a3b8'
                }} />
                {freshness || 'MARKET CLOSED'}
              </span>
              {marketStatus && (
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Market: <b>{marketStatus}</b>
                </span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.35rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <span>Lot Size: <b>1</b></span>
              <span>Tick: <b>0.05</b></span>
              <span>Your Holding: <b style={{ color: 'var(--text-primary)' }}>{ownedQty}</b> shares</span>
            </div>
          </div>

          {/* Live LTP & Change */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ textAlign: 'right' }}>
              <div className="mono tabular-nums" style={{ fontSize: '1.8rem', fontWeight: 800 }}>
                ₹{currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className={isUp ? 'text-profit' : 'text-loss'} style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                {isUp ? '+' : ''}{changePct.toFixed(2)}% ({isUp ? '+' : ''}₹{changeVal.toFixed(2)})
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => { setOrderSide('BUY'); }}
                className="btn btn-buy"
                style={{ padding: '0.45rem 1rem', fontSize: '0.825rem' }}
              >
                <ArrowUpRight size={15} /> Buy
              </button>
              <button
                onClick={() => { setOrderSide('SELL'); }}
                className="btn btn-sell"
                style={{ padding: '0.45rem 1rem', fontSize: '0.825rem' }}
              >
                <ArrowDownRight size={15} /> Sell
              </button>
            </div>
          </div>
        </div>

        {/* Market Stats Bar: Open, High, Low, Prev Close, Volume, Timestamp */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: '0.5rem',
          paddingTop: '0.65rem',
          borderTop: '1px solid var(--border)',
          fontSize: '0.75rem'
        }} className="mono">
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Open: </span>
            <span style={{ fontWeight: 600 }}>{openPrice ? `₹${openPrice.toFixed(2)}` : '—'}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>High: </span>
            <span style={{ fontWeight: 600, color: 'var(--profit)' }}>{highPrice ? `₹${highPrice.toFixed(2)}` : '—'}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Low: </span>
            <span style={{ fontWeight: 600, color: 'var(--loss)' }}>{lowPrice ? `₹${lowPrice.toFixed(2)}` : '—'}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Prev Close: </span>
            <span style={{ fontWeight: 600 }}>{prevClose ? `₹${prevClose.toFixed(2)}` : '—'}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Volume: </span>
            <span style={{ fontWeight: 600 }}>{volume ? Number(volume).toLocaleString('en-IN') : '—'}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Updated: </span>
            <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
              {quoteTimestamp ? new Date(quoteTimestamp).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }) + ' IST' : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Primary Trading Workspace: Left (Chart & Indicators) + Right (Order Panel) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '1.25rem', alignItems: 'start' }}>
        {/* Left Column: Candlestick Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Chart Card */}
          <div className="card" style={{ padding: '1rem' }}>
            {/* Timeframe Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                {['1m', '5m', '15m', '1h', '1d'].map(tf => (
                  <button
                    key={tf}
                    onClick={() => setActiveTimeframe(tf)}
                    style={{
                      background: activeTimeframe === tf ? 'var(--primary)' : 'var(--surface-muted)',
                      color: activeTimeframe === tf ? '#fff' : 'var(--text-secondary)',
                      border: 'none',
                      borderRadius: '5px',
                      padding: '0.3rem 0.65rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {tf.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Quick Indicator Strip */}
              {indicators && (
                <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }} className="mono">
                  <span>EMA20: <b style={{ color: 'var(--text-primary)' }}>₹{indicators.ema_20}</b></span>
                  <span>RSI14: <b style={{ color: indicators.rsi_14 > 70 ? 'var(--loss)' : indicators.rsi_14 < 30 ? 'var(--profit)' : 'var(--text-primary)' }}>{indicators.rsi_14}</b></span>
                  <span>VWAP: <b style={{ color: 'var(--text-primary)' }}>₹{indicators.vwap}</b></span>
                </div>
              )}
            </div>

            {/* Interactive Candle Chart */}
            <div style={{ height: '420px', width: '100%' }}>
              <PriceChart
                symbol={sym}
                timeframe={activeTimeframe}
                initialCandles={candles}
                currentPrice={currentPrice}
              />
            </div>
          </div>

          {/* Bottom Tabs Card */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
              <button
                onClick={() => setActiveBottomTab('INDICATORS')}
                style={{
                  background: activeBottomTab === 'INDICATORS' ? 'var(--surface-muted)' : 'transparent',
                  color: activeBottomTab === 'INDICATORS' ? 'var(--primary)' : 'var(--text-secondary)',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.45rem 0.9rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Technical Indicators
              </button>
              <button
                onClick={() => setActiveBottomTab('SETUP')}
                style={{
                  background: activeBottomTab === 'SETUP' ? 'var(--surface-muted)' : 'transparent',
                  color: activeBottomTab === 'SETUP' ? 'var(--primary)' : 'var(--text-secondary)',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.45rem 0.9rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Strategy & Trade Setup
              </button>
              <button
                onClick={() => setActiveBottomTab('FUNDAMENTALS')}
                style={{
                  background: activeBottomTab === 'FUNDAMENTALS' ? 'var(--surface-muted)' : 'transparent',
                  color: activeBottomTab === 'FUNDAMENTALS' ? 'var(--primary)' : 'var(--text-secondary)',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.45rem 0.9rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Fundamentals & Financials
              </button>
              <button
                onClick={() => setActiveBottomTab('OPTIONS')}
                style={{
                  background: activeBottomTab === 'OPTIONS' ? 'var(--surface-muted)' : 'transparent',
                  color: activeBottomTab === 'OPTIONS' ? 'var(--primary)' : 'var(--text-secondary)',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.45rem 0.9rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Option Chain (F&O)
              </button>
            </div>

            {activeBottomTab === 'INDICATORS' && indicators && (
              <IndicatorPanel symbol={sym} indicators={indicators} />
            )}

            {activeBottomTab === 'FUNDAMENTALS' && (
              <div>
                {fundamentals ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Header info */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                      <div>
                        <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>{fundamentals.company_name || sym}</h4>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          Sector: <b>{fundamentals.sector || 'N/A'}</b> &bull; Industry: <b>{fundamentals.industry || 'N/A'}</b>
                        </div>
                      </div>
                      <span className="badge badge-blue" style={{ fontSize: '0.7rem' }}>
                        Source: {fundamentals.provider || 'yfinance'}
                      </span>
                    </div>

                    {/* Key Ratios Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.75rem' }}>
                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Market Cap</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.market_cap != null
                            ? `₹${(fundamentals.market_cap >= 1e7 ? (fundamentals.market_cap / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 1 }) + ' Cr' : fundamentals.market_cap.toLocaleString('en-IN'))}`
                            : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>P/E Ratio</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.pe_ratio != null ? fundamentals.pe_ratio.toFixed(2) : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Forward P/E</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.forward_pe != null ? fundamentals.forward_pe.toFixed(2) : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>EPS (TTM)</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.eps != null ? `₹${fundamentals.eps.toFixed(2)}` : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Book Value</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.book_value != null ? `₹${fundamentals.book_value.toFixed(2)}` : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>P/B Ratio</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.pb_ratio != null ? fundamentals.pb_ratio.toFixed(2) : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Dividend Yield</div>
                        <div className="mono font-bold text-profit" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.dividend_yield != null ? `${(fundamentals.dividend_yield * 100).toFixed(2)}%` : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Debt-to-Equity</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.debt_to_equity != null ? fundamentals.debt_to_equity.toFixed(2) : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ROE</div>
                        <div className="mono font-bold text-profit" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.roe != null ? `${(fundamentals.roe * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>

                      <div className="card" style={{ padding: '0.75rem', background: 'var(--surface-muted)' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Profit Margin</div>
                        <div className="mono font-bold" style={{ fontSize: '0.95rem', marginTop: '2px' }}>
                          {fundamentals.profit_margin != null ? `${(fundamentals.profit_margin * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                    </div>

                    {/* Financial Statements Table (if available) */}
                    {fundamentals.income_statement && fundamentals.income_statement.length > 0 && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <h5 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                          Annual Financial Highlights (Income Statement)
                        </h5>
                        <div style={{ overflowX: 'auto' }}>
                          <table className="data-table" style={{ fontSize: '0.75rem' }}>
                            <thead>
                              <tr>
                                <th>Financial Metric</th>
                                {Object.keys(fundamentals.income_statement[0]?.values || {}).map((col) => (
                                  <th key={col} style={{ textAlign: 'right' }}>{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {fundamentals.income_statement.slice(0, 8).map((row: any, idx: number) => (
                                <tr key={idx}>
                                  <td style={{ fontWeight: 600 }}>{row.metric}</td>
                                  {Object.keys(fundamentals.income_statement[0]?.values || {}).map((col) => (
                                    <td key={col} style={{ textAlign: 'right' }} className="mono">
                                      {row.values[col] != null
                                        ? `₹${(Math.abs(row.values[col]) >= 1e7 ? (row.values[col] / 1e7).toFixed(1) + ' Cr' : row.values[col].toLocaleString('en-IN'))}`
                                        : 'N/A'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    {isLoadingFundamentals ? 'Loading company fundamentals...' : 'Fundamentals not available for this instrument.'}
                  </div>
                )}
              </div>
            )}

            {activeBottomTab === 'OPTIONS' && (
              <div>
                {/* Options Header Controls */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Expiry:</label>
                    <select
                      value={selectedExpiry}
                      onChange={(e) => setSelectedExpiry(e.target.value)}
                      className="input"
                      style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem', width: 'auto' }}
                    >
                      {optionChain?.expiries?.map((exp: string) => (
                        <option key={exp} value={exp}>{exp}</option>
                      ))}
                    </select>
                    {isLoadingOptions && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Refreshing...</span>}
                  </div>

                  {optionChain && (
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', alignItems: 'center' }} className="mono">
                      <span>Underlying: <b>₹{optionChain.underlying_price}</b></span>
                      <span>Max Pain: <b>₹{optionChain.max_pain}</b></span>
                      <span>PCR: <b className={Number(optionChain.pcr_ratio) >= 1.0 ? 'text-profit' : 'text-loss'}>{optionChain.pcr_ratio}</b></span>
                    </div>
                  )}
                </div>

                {optionChain && optionChain.chain?.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table" style={{ fontSize: '0.75rem', textAlign: 'center' }}>
                      <thead>
                        <tr>
                          <th colSpan={4} style={{ textAlign: 'center', background: 'rgba(34, 197, 94, 0.1)', color: 'var(--profit)' }}>
                            CALLS (CE)
                          </th>
                          <th style={{ textAlign: 'center', background: 'var(--surface-muted)' }}>STRIKE</th>
                          <th colSpan={4} style={{ textAlign: 'center', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--loss)' }}>
                            PUTS (PE)
                          </th>
                        </tr>
                        <tr>
                          <th style={{ textAlign: 'right' }}>OI</th>
                          <th style={{ textAlign: 'right' }}>Vol</th>
                          <th style={{ textAlign: 'right' }}>IV</th>
                          <th style={{ textAlign: 'right' }}>LTP (₹)</th>
                          <th style={{ textAlign: 'center' }}>Strike</th>
                          <th style={{ textAlign: 'left' }}>LTP (₹)</th>
                          <th style={{ textAlign: 'left' }}>IV</th>
                          <th style={{ textAlign: 'left' }}>Vol</th>
                          <th style={{ textAlign: 'left' }}>OI</th>
                        </tr>
                      </thead>
                      <tbody>
                        {optionChain.chain.map((row: any) => {
                          const isAtm = Math.abs(row.strike - optionChain.underlying_price) < 25;
                          const callItm = row.call?.in_the_money;
                          const putItm = row.put?.in_the_money;

                          return (
                            <tr key={row.strike} style={{ background: isAtm ? 'rgba(59, 130, 246, 0.08)' : undefined }}>
                              {/* Call columns */}
                              <td style={{ textAlign: 'right', background: callItm ? 'rgba(34, 197, 94, 0.04)' : undefined }} className="mono">
                                {row.call?.open_interest ? (row.call.open_interest / 1000).toFixed(1) + 'k' : '—'}
                              </td>
                              <td style={{ textAlign: 'right', background: callItm ? 'rgba(34, 197, 94, 0.04)' : undefined }} className="mono">
                                {row.call?.volume ? (row.call.volume / 1000).toFixed(1) + 'k' : '—'}
                              </td>
                              <td style={{ textAlign: 'right', background: callItm ? 'rgba(34, 197, 94, 0.04)' : undefined }} className="mono text-muted">
                                {row.call?.implied_volatility ? (row.call.implied_volatility * 100).toFixed(1) + '%' : '—'}
                              </td>
                              <td
                                style={{
                                  textAlign: 'right',
                                  cursor: 'pointer',
                                  fontWeight: 700,
                                  background: callItm ? 'rgba(34, 197, 94, 0.07)' : undefined
                                }}
                                className="mono text-profit"
                                onClick={() => {
                                  if (row.call) {
                                    setLimitPrice(row.call.last_price);
                                    setOrderType('LIMIT');
                                    setOrderSide('BUY');
                                    showToast(`Selected CE ${row.strike} @ ₹${row.call.last_price}`, 'info');
                                  }
                                }}
                                title="Click to trade Call"
                              >
                                ₹{row.call?.last_price?.toFixed(2) ?? '—'}
                              </td>

                              {/* Strike column */}
                              <td style={{ textAlign: 'center', fontWeight: 700 }} className="mono font-bold">
                                {row.strike}
                              </td>

                              {/* Put columns */}
                              <td
                                style={{
                                  textAlign: 'left',
                                  cursor: 'pointer',
                                  fontWeight: 700,
                                  background: putItm ? 'rgba(239, 68, 68, 0.07)' : undefined
                                }}
                                className="mono text-loss"
                                onClick={() => {
                                  if (row.put) {
                                    setLimitPrice(row.put.last_price);
                                    setOrderType('LIMIT');
                                    setOrderSide('BUY');
                                    showToast(`Selected PE ${row.strike} @ ₹${row.put.last_price}`, 'info');
                                  }
                                }}
                                title="Click to trade Put"
                              >
                                ₹{row.put?.last_price?.toFixed(2) ?? '—'}
                              </td>
                              <td style={{ textAlign: 'left', background: putItm ? 'rgba(239, 68, 68, 0.04)' : undefined }} className="mono text-muted">
                                {row.put?.implied_volatility ? (row.put.implied_volatility * 100).toFixed(1) + '%' : '—'}
                              </td>
                              <td style={{ textAlign: 'left', background: putItm ? 'rgba(239, 68, 68, 0.04)' : undefined }} className="mono">
                                {row.put?.volume ? (row.put.volume / 1000).toFixed(1) + 'k' : '—'}
                              </td>
                              <td style={{ textAlign: 'left', background: putItm ? 'rgba(239, 68, 68, 0.04)' : undefined }} className="mono">
                                {row.put?.open_interest ? (row.put.open_interest / 1000).toFixed(1) + 'k' : '—'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    {isLoadingOptions ? 'Loading option chain...' : 'Option chain not available for this instrument.'}
                  </div>
                )}
              </div>
            )}

            {activeBottomTab === 'SETUP' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Automated rule-based swing and intraday trade setup with risk-reward parameters.
                  </p>
                  <button
                    onClick={handleFetchTradeSetup}
                    disabled={riskValidating}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                  >
                    <Sparkles size={14} /> {riskValidating ? 'Generating...' : 'Calculate Setup'}
                  </button>
                </div>

                {tradeSetup ? (
                  <div style={{ background: 'var(--surface-muted)', borderRadius: '8px', padding: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <span className={`badge ${tradeSetup.side === 'BUY' ? 'badge-green' : 'badge-red'}`} style={{ fontSize: '0.85rem' }}>
                        {tradeSetup.side} SETUP
                      </span>
                      <span className="mono" style={{ fontSize: '0.8rem' }}>R:R {tradeSetup.risk_reward}:1</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontSize: '0.825rem' }} className="mono">
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Quantity:</span>
                        <div style={{ fontWeight: 700 }}>{tradeSetup.quantity}</div>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Stop Loss:</span>
                        <div style={{ color: 'var(--loss)', fontWeight: 700 }}>₹{Number(tradeSetup.stop_loss).toFixed(2)}</div>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Target:</span>
                        <div style={{ color: 'var(--profit)', fontWeight: 700 }}>₹{Number(tradeSetup.target_price).toFixed(2)}</div>
                      </div>
                    </div>

                    {tradeSetup.reasons && (
                      <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        <b>Setup Factors:</b>
                        <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem' }}>
                          {tradeSetup.reasons.map((r: string, idx: number) => (
                            <li key={idx}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Click "Calculate Setup" to generate automated technical entry/exit criteria.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: In-Workspace Paper Trading Order Panel */}
        <div className="card" style={{ position: 'sticky', top: '1rem', padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Paper Order Panel
            </h3>
            <span className="paper-badge" style={{ fontSize: '0.65rem' }}>SIMULATED</span>
          </div>

          {/* BUY / SELL Switcher */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
            <button
              type="button"
              onClick={() => setOrderSide('BUY')}
              className={`btn ${orderSide === 'BUY' ? 'btn-buy' : 'btn-secondary'}`}
              style={{ fontWeight: 700 }}
            >
              <ArrowUpRight size={15} /> BUY
            </button>
            <button
              type="button"
              onClick={() => setOrderSide('SELL')}
              className={`btn ${orderSide === 'SELL' ? 'btn-sell' : 'btn-secondary'}`}
              style={{ fontWeight: 700 }}
            >
              <ArrowDownRight size={15} /> SELL
            </button>
          </div>

          <form onSubmit={handlePlaceOrder} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {/* Order Type */}
            <div>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                Order Type
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setOrderType('MARKET')}
                  style={{
                    padding: '0.4rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: orderType === 'MARKET' ? 'var(--primary)' : 'var(--surface-muted)',
                    color: orderType === 'MARKET' ? '#fff' : 'var(--text-secondary)',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    cursor: 'pointer'
                  }}
                >
                  MARKET
                </button>
                <button
                  type="button"
                  onClick={() => setOrderType('LIMIT')}
                  style={{
                    padding: '0.4rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: orderType === 'LIMIT' ? 'var(--primary)' : 'var(--surface-muted)',
                    color: orderType === 'LIMIT' ? '#fff' : 'var(--text-secondary)',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    cursor: 'pointer'
                  }}
                >
                  LIMIT
                </button>
              </div>
            </div>

            {/* Quantity */}
            <div>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                Quantity (Shares)
              </label>
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={e => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                className="input mono tabular-nums"
                required
              />
            </div>

            {/* Limit Price */}
            {orderType === 'LIMIT' && (
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                  Limit Price (₹)
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={limitPrice || ''}
                  onChange={e => setLimitPrice(parseFloat(e.target.value) || 0)}
                  className="input mono tabular-nums"
                  required
                />
              </div>
            )}

            {/* Stop Loss & Target */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                  Stop Loss (₹)
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={stopLoss || ''}
                  onChange={e => setStopLoss(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="input mono tabular-nums"
                  placeholder={orderSide === 'BUY' ? `< ₹${currentPrice}` : `> ₹${currentPrice}`}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                  Target (₹)
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={target || ''}
                  onChange={e => setTarget(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="input mono tabular-nums"
                  placeholder={orderSide === 'BUY' ? `> ₹${currentPrice}` : `< ₹${currentPrice}`}
                />
              </div>
            </div>

            {/* Calculations Breakdown */}
            <div style={{ background: 'var(--surface-muted)', borderRadius: '8px', padding: '0.75rem', fontSize: '0.78rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Estimated Value:</span>
                <span className="mono tabular-nums" style={{ fontWeight: 600 }}>₹{orderTurnover.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Simulated Charges:</span>
                <span className="mono tabular-nums" style={{ color: 'var(--text-muted)' }}>₹{estimatedCharges.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border)', paddingTop: '0.35rem', marginTop: '0.35rem' }}>
                <span style={{ fontWeight: 600 }}>Total Required:</span>
                <span className="mono tabular-nums" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  ₹{totalCost.toFixed(2)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                <span>Available Cash:</span>
                <span className="mono tabular-nums">₹{availableCash.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={orderSubmitting}
              className={`btn ${orderSide === 'BUY' ? 'btn-buy' : 'btn-sell'}`}
              style={{ width: '100%', padding: '0.65rem', fontWeight: 700, marginTop: '0.25rem' }}
            >
              <Lock size={15} />
              <span>{orderSubmitting ? 'Placing Paper Order...' : `${orderSide} ${sym} (PAPER)`}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default StockDetail;
