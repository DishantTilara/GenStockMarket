import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../context/WebSocketContext';
import { TradeExecutionModal } from '../components/TradeExecutionModal';
import { 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  XSquare, 
  PlusCircle, 
  MinusCircle, 
  Settings2,
  DollarSign
} from 'lucide-react';

interface PositionItem {
  id: string;
  symbol: string;
  sector?: string;
  quantity: number;
  average_price: number;
  current_price: number;
  invested_amount: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  realized_pnl: number;
  stop_loss?: number;
  target_price?: number;
}

export const Positions: React.FC = () => {
  const [openPositions, setOpenPositions] = useState<PositionItem[]>([]);
  const [closedPositions, setClosedPositions] = useState<PositionItem[]>([]);
  const [totalUnrealized, setTotalUnrealized] = useState(0);
  const [totalRealized, setTotalRealized] = useState(0);
  const [totalCurrentVal, setTotalCurrentVal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'OPEN' | 'CLOSED'>('OPEN');
  
  // Trade Modal
  const [tradeModalOpen, setTradeModalOpen] = useState(false);
  const [tradeSymbol, setTradeSymbol] = useState('RELIANCE');
  const [tradeSide, setTradeSide] = useState<'BUY' | 'SELL'>('BUY');

  // Modify SL/Target Modal
  const [modifyModalOpen, setModifyModalOpen] = useState(false);
  const [modifyingPos, setModifyingPos] = useState<PositionItem | null>(null);
  const [newSl, setNewSl] = useState<number | undefined>();
  const [newTarget, setNewTarget] = useState<number | undefined>();

  const { showToast } = useToast();
  const { marketTicks } = useWebSocket();
  const navigate = useNavigate();

  const fetchPositions = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getPositions();
      setOpenPositions(data.open_positions || []);
      setClosedPositions(data.closed_positions || []);
      setTotalUnrealized(data.total_unrealized_pnl || 0);
      setTotalRealized(data.total_realized_pnl || 0);
      setTotalCurrentVal(data.total_current_value || 0);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch positions', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPositions();
  }, []);

  // Update LTP live from WebSocket ticks
  useEffect(() => {
    if (Object.keys(marketTicks).length === 0) return;
    setOpenPositions(prev =>
      prev.map(p => {
        const tick = marketTicks[p.symbol];
        if (!tick) return p;
        const cur = tick.price;
        const val = cur * p.quantity;
        const invested = p.average_price * p.quantity;
        const pnl = val - invested;
        const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;
        return {
          ...p,
          current_price: cur,
          current_value: val,
          unrealized_pnl: pnl,
          unrealized_pnl_pct: pnlPct
        };
      })
    );
  }, [marketTicks]);

  const handleClosePosition = async (symbol: string) => {
    if (!window.confirm(`Confirm immediate market exit for position ${symbol}?`)) return;
    try {
      const res = await ApiClient.closePosition(symbol);
      showToast(`Closed ${symbol} @ ₹${res.execution_price} (P&L: ₹${res.realized_pnl})`, 'success');
      fetchPositions();
    } catch (err: any) {
      showToast(err.message || 'Failed to close position', 'error');
    }
  };

  const openModifyModal = (pos: PositionItem) => {
    setModifyingPos(pos);
    setNewSl(pos.stop_loss);
    setNewTarget(pos.target_price);
    setModifyModalOpen(true);
  };

  const submitModifySlTarget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modifyingPos) return;
    try {
      await ApiClient.modifyPositionSlTarget(modifyingPos.symbol, newSl, newTarget);
      showToast(`Updated risk bounds for ${modifyingPos.symbol}`, 'success');
      setModifyModalOpen(false);
      fetchPositions();
    } catch (err: any) {
      showToast(err.message || 'Failed to modify SL/Target', 'error');
    }
  };

  const openTradeModal = (symbol: string, side: 'BUY' | 'SELL') => {
    setTradeSymbol(symbol);
    setTradeSide(side);
    setTradeModalOpen(true);
  };

  const displayedPositions = activeTab === 'OPEN' ? openPositions : closedPositions;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Positions</h1>
            <span className="paper-badge">PAPER TRADING • REALTIME P&L</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Open trading holdings and realized performance
          </p>
        </div>

        <button 
          onClick={fetchPositions} 
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '0.45rem 0.85rem' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Position Value
          </div>
          <div className="mono tabular-nums" style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.25rem' }}>
            ₹{totalCurrentVal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            {openPositions.length} active position{openPositions.length === 1 ? '' : 's'}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Unrealized P&L
          </div>
          <div className={`mono tabular-nums ${totalUnrealized >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.25rem' }}>
            {totalUnrealized >= 0 ? '+' : ''}₹{totalUnrealized.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            Mark-to-market live P&L
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Realized P&L
          </div>
          <div className={`mono tabular-nums ${totalRealized >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.25rem' }}>
            {totalRealized >= 0 ? '+' : ''}₹{totalRealized.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            Booked trading profits/losses
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        <button
          onClick={() => setActiveTab('OPEN')}
          style={{
            padding: '0.45rem 1rem',
            fontSize: '0.825rem',
            fontWeight: 600,
            background: activeTab === 'OPEN' ? 'var(--surface-muted)' : 'transparent',
            color: activeTab === 'OPEN' ? 'var(--primary)' : 'var(--text-secondary)',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Open Positions ({openPositions.length})
        </button>
        <button
          onClick={() => setActiveTab('CLOSED')}
          style={{
            padding: '0.45rem 1rem',
            fontSize: '0.825rem',
            fontWeight: 600,
            background: activeTab === 'CLOSED' ? 'var(--surface-muted)' : 'transparent',
            color: activeTab === 'CLOSED' ? 'var(--primary)' : 'var(--text-secondary)',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Closed Positions ({closedPositions.length})
        </button>
      </div>

      {/* Positions Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Qty</th>
                <th>Avg Price</th>
                <th>LTP</th>
                <th>Invested</th>
                <th>Current Value</th>
                <th>P&L</th>
                <th>P&L %</th>
                <th>SL</th>
                <th>Target</th>
                {activeTab === 'OPEN' && <th style={{ textAlign: 'right' }}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    Loading positions...
                  </td>
                </tr>
              ) : displayedPositions.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    {activeTab === 'OPEN' 
                      ? 'No open holdings. Visit Stock Detail or Watchlist to place paper BUY orders.'
                      : 'No closed positions history.'}
                  </td>
                </tr>
              ) : (
                displayedPositions.map(pos => {
                  const pnl = activeTab === 'OPEN' ? pos.unrealized_pnl : pos.realized_pnl;
                  const isProfit = pnl >= 0;

                  return (
                    <tr key={pos.id}>
                      <td>
                        <div 
                          onClick={() => navigate(`/stock/${pos.symbol}`)}
                          style={{ cursor: 'pointer', display: 'inline-flex', flexDirection: 'column' }}
                        >
                          <span style={{ fontWeight: 700, color: 'var(--primary)' }}>{pos.symbol}</span>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{pos.sector || 'NSE'}</span>
                        </div>
                      </td>
                      <td className="mono tabular-nums">{pos.quantity}</td>
                      <td className="mono tabular-nums">₹{Number(pos.average_price).toFixed(2)}</td>
                      <td className="mono tabular-nums">₹{Number(pos.current_price).toFixed(2)}</td>
                      <td className="mono tabular-nums">₹{Number(pos.invested_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="mono tabular-nums">₹{Number(pos.current_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className={`mono tabular-nums ${isProfit ? 'text-profit' : 'text-loss'}`} style={{ fontWeight: 700 }}>
                        {isProfit ? '+' : ''}₹{Number(pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className={`mono tabular-nums ${isProfit ? 'text-profit' : 'text-loss'}`} style={{ fontWeight: 600 }}>
                        {activeTab === 'OPEN' ? (
                          `${pos.unrealized_pnl_pct >= 0 ? '+' : ''}${Number(pos.unrealized_pnl_pct).toFixed(2)}%`
                        ) : '—'}
                      </td>
                      <td className="mono tabular-nums" style={{ color: 'var(--text-muted)' }}>
                        {pos.stop_loss ? `₹${Number(pos.stop_loss).toFixed(2)}` : '—'}
                      </td>
                      <td className="mono tabular-nums" style={{ color: 'var(--text-muted)' }}>
                        {pos.target_price ? `₹${Number(pos.target_price).toFixed(2)}` : '—'}
                      </td>
                      {activeTab === 'OPEN' && (
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                            <button
                              onClick={() => openTradeModal(pos.symbol, 'BUY')}
                              title="Buy More Shares"
                              className="btn btn-secondary"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            >
                              <PlusCircle size={13} color="var(--profit)" /> Buy More
                            </button>
                            <button
                              onClick={() => openTradeModal(pos.symbol, 'SELL')}
                              title="Sell Shares"
                              className="btn btn-secondary"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            >
                              <MinusCircle size={13} color="var(--loss)" /> Sell
                            </button>
                            <button
                              onClick={() => openModifyModal(pos)}
                              title="Modify SL & Target"
                              className="btn btn-secondary"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            >
                              <Settings2 size={13} />
                            </button>
                            <button
                              onClick={() => handleClosePosition(pos.symbol)}
                              title="Close Position (Exit at Market)"
                              className="btn btn-outline-danger"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            >
                              <XSquare size={13} /> Exit
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modify SL/Target Modal */}
      {modifyModalOpen && modifyingPos && (
        <div className="modal-overlay" onClick={() => setModifyModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '420px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Set Risk Controls ({modifyingPos.symbol})
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Set automated paper Stop-Loss and Target exit triggers.
            </p>

            <form onSubmit={submitModifySlTarget} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Stop-Loss Threshold (₹)
                </label>
                <input 
                  type="number" 
                  step="0.05" 
                  value={newSl || ''} 
                  onChange={e => setNewSl(e.target.value ? parseFloat(e.target.value) : undefined)} 
                  className="input" 
                  placeholder={`Below current ₹${modifyingPos.current_price}`} 
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Target Price (₹)
                </label>
                <input 
                  type="number" 
                  step="0.05" 
                  value={newTarget || ''} 
                  onChange={e => setNewTarget(e.target.value ? parseFloat(e.target.value) : undefined)} 
                  className="input" 
                  placeholder={`Above current ₹${modifyingPos.current_price}`} 
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setModifyModalOpen(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Triggers
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quick Trade Execution Modal */}
      {tradeModalOpen && (
        <TradeExecutionModal
          isOpen={tradeModalOpen}
          onClose={() => {
            setTradeModalOpen(false);
            fetchPositions();
          }}
          symbol={tradeSymbol}
          defaultSide={tradeSide}
        />
      )}
    </div>
  );
};

export default Positions;
