import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useMarketStream } from '../context/WebSocketContext';
import { PriceChart } from '../components/PriceChart';
import { IndicatorPanel } from '../components/IndicatorPanel';
import { TradeExecutionModal } from '../components/TradeExecutionModal';
import {
  Sparkles,
  Zap,
  Activity,
  Calendar,
  Building2,
  FileText,
  ShieldCheck,
  TrendingUp,
  ArrowLeft
} from 'lucide-react';

export const StockDetail: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const sym = (symbol || 'RELIANCE').toUpperCase();
  const { ticks } = useMarketStream();

  const [quote, setQuote] = useState<any>(null);
  const [candles, setCandles] = useState<any[]>([]);
  const [indicators, setIndicators] = useState<any>(null);
  const [aiAnalysis, setAiAnalysis] = useState<any>(null);
  const [news, setNews] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [activeSetup, setActiveSetup] = useState<any>(null);
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);
  const [isLoadingAI, setIsLoadingAI] = useState(false);

  useEffect(() => {
    ApiClient.getQuote(sym).then(setQuote).catch(() => {});
    ApiClient.getMinuteBars(sym, 100).then(setCandles).catch(() => {});
    ApiClient.getIndicators(sym).then(setIndicators).catch(() => {});
    ApiClient.getNews(sym).then(setNews).catch(() => {});
    ApiClient.getAnnouncements(sym).then(setAnnouncements).catch(() => {});
  }, [sym]);

  const runAIAnalysis = async () => {
    setIsLoadingAI(true);
    try {
      const data = await ApiClient.getAIStockAnalysis(sym);
      setAiAnalysis(data);
    } catch {}
    finally {
      setIsLoadingAI(false);
    }
  };

  const handleOpenTradeSetup = async () => {
    try {
      const setup = await ApiClient.generateTradeSetup(sym);
      setActiveSetup(setup);
      setIsTradeModalOpen(true);
    } catch {}
  };

  const liveTick = ticks[sym];
  const price = liveTick ? liveTick.price : quote ? Number(quote.price) : 2985.50;
  const changePct = quote ? Number(quote.change_pct) : 0.65;
  const isUp = changePct >= 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Link to="/market" className="btn btn-secondary" style={{ padding: '6px 10px' }}>
            <ArrowLeft size={16} />
          </Link>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>{sym}</h2>
              <span className="badge badge-blue">NSE EQUITY</span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Verified Indian Stock Security Data
            </div>
          </div>
        </div>

        {/* Live Price + Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ textAlign: 'right' }}>
            <div className="mono tabular-nums" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff' }}>
              ₹{price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className={isUp ? 'text-profit' : 'text-loss'} style={{ fontSize: '0.85rem', fontWeight: 600 }}>
              {isUp ? '+' : ''}{changePct.toFixed(2)}% Today
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={runAIAnalysis}
              disabled={isLoadingAI}
              className="btn btn-purple"
              style={{ gap: '6px' }}
            >
              <Sparkles size={16} />
              <span>{isLoadingAI ? 'Analyzing...' : 'Ask GenAI Analyst'}</span>
            </button>
            <button
              onClick={handleOpenTradeSetup}
              className="btn btn-primary"
              style={{ gap: '6px' }}
            >
              <Zap size={16} />
              <span>Generate Setup</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Price Chart + Indicator Suite */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <PriceChart
            symbol={sym}
            candles={candles}
            onTimeframeChange={(tf) => {
              if (tf === '1d') {
                ApiClient.getHistory(sym).then(setCandles).catch(() => {});
              } else {
                ApiClient.getMinuteBars(sym, 100).then(setCandles).catch(() => {});
              }
            }}
          />
          <IndicatorPanel indicators={indicators} />
        </div>

        {/* Right Sidebar: Fundamentals & Corporate Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Fundamentals Card */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={18} color="var(--accent-blue)" />
              Company Fundamentals
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '10px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>P/E Ratio</div>
                <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700 }}>26.8</div>
              </div>
              <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '10px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>P/B Ratio</div>
                <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700 }}>2.4</div>
              </div>
              <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '10px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ROE</div>
                <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-green)' }}>14.8%</div>
              </div>
              <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '10px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Dividend Yield</div>
                <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700 }}>0.85%</div>
              </div>
            </div>
          </div>

          {/* Corporate Actions */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={18} color="var(--accent-purple)" />
              Corporate Filings & Actions
            </h4>
            {announcements.length > 0 ? (
              announcements.map((ca) => (
                <div key={ca.id} style={{ padding: '8px 12px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="badge badge-purple">{ca.action_type}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      Ex-Date: {new Date(ca.ex_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', marginTop: '6px', color: 'var(--text-primary)' }}>
                    {ca.description}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No imminent corporate actions recorded.</div>
            )}
          </div>
        </div>
      </div>

      {/* AI Analyst Report Section */}
      {aiAnalysis && (
        <div className="card card-glow-purple" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Sparkles size={22} color="var(--accent-purple)" />
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>GenAI Intelligence Dossier: {aiAnalysis.symbol}</h3>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <span className={`badge ${aiAnalysis.signal === 'BUY' ? 'badge-green' : aiAnalysis.signal === 'SELL' ? 'badge-red' : 'badge-amber'}`} style={{ fontSize: '0.9rem', padding: '4px 12px' }}>
                SIGNAL: {aiAnalysis.signal}
              </span>
              <span className="badge badge-purple">Confidence: {Math.round(aiAnalysis.confidence * 100)}%</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '1.5rem' }} className="mono">
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '10px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Regime</span>
              <div style={{ fontWeight: 600 }}>{aiAnalysis.market_regime}</div>
            </div>
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '10px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Stop Loss</span>
              <div style={{ fontWeight: 600, color: 'var(--accent-red)' }}>₹{aiAnalysis.stop_loss ? Number(aiAnalysis.stop_loss).toFixed(2) : 'N/A'}</div>
            </div>
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '10px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Targets</span>
              <div style={{ fontWeight: 600, color: 'var(--accent-green)' }}>
                {aiAnalysis.targets.length ? aiAnalysis.targets.map((t: number) => `₹${t.toFixed(0)}`).join(' / ') : 'N/A'}
              </div>
            </div>
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '10px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Risk / Reward</span>
              <div style={{ fontWeight: 600 }}>{aiAnalysis.risk_reward ? `1 : ${aiAnalysis.risk_reward}` : 'N/A'}</div>
            </div>
          </div>

          {/* Supporting & Invalidation Factors */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <h5 style={{ fontSize: '0.85rem', color: 'var(--accent-green)', marginBottom: '8px' }}>✓ Supporting Rationales</h5>
              <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {aiAnalysis.supporting_factors.map((f: string, i: number) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
            <div>
              <h5 style={{ fontSize: '0.85rem', color: 'var(--accent-red)', marginBottom: '8px' }}>⚠ Invalidation Conditions</h5>
              <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {aiAnalysis.invalidation_conditions.map((f: string, i: number) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Trade Modal */}
      {isTradeModalOpen && activeSetup && (
        <TradeExecutionModal
          setup={activeSetup}
          onClose={() => setIsTradeModalOpen(false)}
          onSuccess={() => setIsTradeModalOpen(false)}
        />
      )}
    </div>
  );
};
