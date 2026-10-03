import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../context/WebSocketContext';
import { ShieldCheck, AlertTriangle, CheckCircle2, X, Lock, ArrowUpRight, ArrowDownRight, Calculator } from 'lucide-react';

interface TradeExecutionModalProps {
  setup?: any;
  symbol?: string;
  defaultSide?: 'BUY' | 'SELL';
  isOpen?: boolean;
  onClose: () => void;
  onSuccess?: (order: any) => void;
}

export const TradeExecutionModal: React.FC<TradeExecutionModalProps> = ({
  setup,
  symbol: initialSymbol,
  defaultSide = 'BUY',
  isOpen = true,
  onClose,
  onSuccess
}) => {
  const activeSymbol = (setup?.symbol || initialSymbol || 'RELIANCE').toUpperCase();
  const [side, setSide] = useState<'BUY' | 'SELL'>(setup?.side || defaultSide);
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [quantity, setQuantity] = useState<number>(setup?.quantity || 10);
  const [limitPrice, setLimitPrice] = useState<number>(0);
  const [stopLoss, setStopLoss] = useState<number | undefined>(setup?.stop_loss);
  const [target, setTarget] = useState<number | undefined>(setup?.target_price);

  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [availableFunds, setAvailableFunds] = useState<number>(0);
  const [ownedQuantity, setOwnedQuantity] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [riskData, setRiskData] = useState<any>(null);
  const [riskValidating, setRiskValidating] = useState(false);
  const [reviewMode, setReviewMode] = useState(false);

  const { showToast } = useToast();
  const { marketTicks } = useWebSocket();

  // Load quote, wallet, and holding on mount
  useEffect(() => {
    const loadMarketAndAccount = async () => {
      try {
        const [quote, wallet, positionsData] = await Promise.all([
          ApiClient.getQuote(activeSymbol),
          ApiClient.getWallet(),
          ApiClient.getPositions()
        ]);
        const price = Number(quote.price);
        setCurrentPrice(price);
        if (!limitPrice) setLimitPrice(price);
        setAvailableFunds(Number(wallet.available_balance));

        const holding = positionsData.open_positions?.find(p => p.symbol === activeSymbol);
        setOwnedQuantity(holding ? holding.quantity : 0);
      } catch (err: any) {
        console.error(err);
      }
    };
    loadMarketAndAccount();
  }, [activeSymbol]);

  // Live price update from WebSocket
  useEffect(() => {
    if (marketTicks[activeSymbol]) {
      const livePrice = marketTicks[activeSymbol].price;
      setCurrentPrice(livePrice);
    }
  }, [marketTicks, activeSymbol]);

  const effectivePrice = orderType === 'MARKET' ? currentPrice : (limitPrice || currentPrice);
  const turnover = effectivePrice * quantity;
  
  // Approximate Indian charges (Brokerage min 20, STT 0.1%, GST 18%, etc ~ 0.12%)
  const estimatedCharges = Math.max(20, turnover * 0.0012);
  const totalRequired = turnover + estimatedCharges;

  // Validate Risk
  const handleValidateRisk = async () => {
    try {
      setRiskValidating(true);
      const res = await ApiClient.validateRisk({
        symbol: activeSymbol,
        side,
        order_type: orderType,
        quantity,
        price: effectivePrice,
        stop_loss: stopLoss,
        target
      });
      setRiskData(res);
      if (res.approved) {
        setReviewMode(true);
      } else {
        showToast(res.rejection_reason || 'Risk check rejected', 'error');
      }
    } catch (err: any) {
      showToast(err.message || 'Risk check failed', 'error');
    } finally {
      setRiskValidating(false);
    }
  };

  const handleExecuteOrder = async () => {
    try {
      setLoading(true);
      const order = await ApiClient.createOrder({
        symbol: activeSymbol,
        side,
        order_type: orderType,
        quantity,
        price: orderType === 'LIMIT' ? limitPrice : undefined,
        stop_loss: stopLoss,
        target_price: target,
        confirmation_token: riskData?.confirmation_token
      });

      showToast(`Paper order placed: ${order.side} ${order.quantity} ${order.symbol} (${order.status})`, 'success');
      if (onSuccess) onSuccess(order);
      onClose();
    } catch (err: any) {
      showToast(err.message || 'Order placement failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const isBuy = side === 'BUY';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '480px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                {isBuy ? 'BUY' : 'SELL'} {activeSymbol}
              </h3>
              <span className="paper-badge">PAPER TRADING</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.2rem' }}>
              <span className="mono" style={{ fontSize: '1rem', fontWeight: 700 }}>
                ₹{currentPrice.toFixed(2)}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Holding: <b style={{ color: 'var(--text-primary)' }}>{ownedQuantity}</b> shares
              </span>
            </div>
          </div>
          <button 
            onClick={onClose} 
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.25rem' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Side Tabs (Buy / Sell) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
          <button
            type="button"
            onClick={() => { setSide('BUY'); setReviewMode(false); }}
            className={`btn ${isBuy ? 'btn-buy' : 'btn-secondary'}`}
            style={{ fontWeight: 700 }}
          >
            <ArrowUpRight size={16} /> BUY
          </button>
          <button
            type="button"
            onClick={() => { setSide('SELL'); setReviewMode(false); }}
            className={`btn ${!isBuy ? 'btn-sell' : 'btn-secondary'}`}
            style={{ fontWeight: 700 }}
          >
            <ArrowDownRight size={16} /> SELL
          </button>
        </div>

        {/* Order Form */}
        {!reviewMode ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
            {/* Order Type */}
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
                Order Type
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setOrderType('MARKET')}
                  style={{
                    padding: '0.45rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: orderType === 'MARKET' ? 'var(--primary)' : 'var(--surface-muted)',
                    color: orderType === 'MARKET' ? '#fff' : 'var(--text-secondary)',
                    fontWeight: 600,
                    fontSize: '0.825rem',
                    cursor: 'pointer'
                  }}
                >
                  MARKET (LTP)
                </button>
                <button
                  type="button"
                  onClick={() => setOrderType('LIMIT')}
                  style={{
                    padding: '0.45rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: orderType === 'LIMIT' ? 'var(--primary)' : 'var(--surface-muted)',
                    color: orderType === 'LIMIT' ? '#fff' : 'var(--text-secondary)',
                    fontWeight: 600,
                    fontSize: '0.825rem',
                    cursor: 'pointer'
                  }}
                >
                  LIMIT
                </button>
              </div>
            </div>

            {/* Quantity & Price */}
            <div style={{ display: 'grid', gridTemplateColumns: orderType === 'LIMIT' ? '1fr 1fr' : '1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
                  Quantity
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

              {orderType === 'LIMIT' && (
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
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
            </div>

            {/* Optional Stop Loss & Target */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
                  Stop Loss (₹)
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={stopLoss || ''}
                  onChange={e => setStopLoss(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="input mono tabular-nums"
                  placeholder={isBuy ? `< ₹${currentPrice}` : `> ₹${currentPrice}`}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
                  Target (₹)
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={target || ''}
                  onChange={e => setTarget(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="input mono tabular-nums"
                  placeholder={isBuy ? `> ₹${currentPrice}` : `< ₹${currentPrice}`}
                />
              </div>
            </div>

            {/* Financial Summary */}
            <div style={{ background: 'var(--surface-muted)', borderRadius: '8px', padding: '0.85rem', marginTop: '0.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Estimated Value:</span>
                <span className="mono tabular-nums" style={{ fontWeight: 600 }}>₹{turnover.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Simulated Charges & Taxes:</span>
                <span className="mono tabular-nums" style={{ color: 'var(--text-muted)' }}>₹{estimatedCharges.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem', marginTop: '0.4rem' }}>
                <span style={{ fontWeight: 600 }}>{isBuy ? 'Required Paper Funds:' : 'Est. Sale Proceeds:'}</span>
                <span className="mono tabular-nums" style={{ fontWeight: 700, color: isBuy ? 'var(--text-primary)' : 'var(--profit)' }}>
                  ₹{totalRequired.toFixed(2)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                <span>Available Paper Cash:</span>
                <span className="mono tabular-nums">₹{availableFunds.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              <button type="button" onClick={onClose} className="btn btn-secondary" style={{ flex: 1 }}>
                Cancel
              </button>
              <button
                type="button"
                onClick={handleValidateRisk}
                disabled={riskValidating}
                className={`btn ${isBuy ? 'btn-buy' : 'btn-sell'}`}
                style={{ flex: 2 }}
              >
                {riskValidating ? 'Checking Risk...' : 'Review Paper Order'}
              </button>
            </div>
          </div>
        ) : (
          /* Review & Confirm Mode */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ background: 'var(--surface-muted)', borderRadius: '8px', padding: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--profit)' }}>
                <CheckCircle2 size={18} />
                <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>Risk Checks Passed</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.65rem', fontSize: '0.8rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Action:</span>
                  <div style={{ fontWeight: 700 }}>{side} {activeSymbol}</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Quantity:</span>
                  <div className="mono tabular-nums" style={{ fontWeight: 700 }}>{quantity} shares</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Order Type:</span>
                  <div style={{ fontWeight: 700 }}>{orderType}</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Execution Price:</span>
                  <div className="mono tabular-nums" style={{ fontWeight: 700 }}>₹{effectivePrice.toFixed(2)}</div>
                </div>
                {stopLoss && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Stop Loss:</span>
                    <div className="mono tabular-nums" style={{ color: 'var(--loss)', fontWeight: 600 }}>₹{stopLoss.toFixed(2)}</div>
                  </div>
                )}
                {target && (
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Target:</span>
                    <div className="mono tabular-nums" style={{ color: 'var(--profit)', fontWeight: 600 }}>₹{target.toFixed(2)}</div>
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button type="button" onClick={() => setReviewMode(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                Back
              </button>
              <button
                type="button"
                onClick={handleExecuteOrder}
                disabled={loading}
                className={`btn ${isBuy ? 'btn-buy' : 'btn-sell'}`}
                style={{ flex: 2, gap: '0.5rem' }}
              >
                <Lock size={15} />
                <span>{loading ? 'Submitting...' : `Confirm Paper ${side}`}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradeExecutionModal;
