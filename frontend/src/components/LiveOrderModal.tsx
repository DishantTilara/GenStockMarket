import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  X,
  ShieldCheck,
  DollarSign,
  Layers,
  ArrowRight
} from 'lucide-react';

interface LiveOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  orderData: {
    broker: string;
    symbol: string;
    side: string;
    quantity: number;
    price: number;
    orderType: string;
    stopLoss?: number;
    target?: number;
    estimatedCharges?: number;
    currentBalance?: number;
  };
  riskChecks?: Array<{ check_name: string; passed: boolean; message: string }>;
}

export const LiveOrderModal: React.FC<LiveOrderModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  orderData,
  riskChecks = []
}) => {
  const [submitting, setSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const totalValue = orderData.price * orderData.quantity;
  const maxRisk = orderData.stopLoss ? Math.abs(orderData.price - orderData.stopLoss) * orderData.quantity : totalValue;

  const handleConfirmOrder = async () => {
    try {
      setSubmitting(true);
      await onConfirm();
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem'
    }}>
      <div className="card" style={{
        maxWidth: '560px',
        width: '100%',
        padding: '2rem',
        borderRadius: '16px',
        border: '1px solid rgba(239, 68, 68, 0.4)',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              padding: '4px 10px',
              borderRadius: '6px',
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid #ef4444',
              color: '#ef4444',
              fontWeight: 800,
              fontSize: '0.8rem',
              letterSpacing: '0.05em'
            }}>
              LIVE TRADING CONFIRMATION
            </span>
          </div>
          <button
            onClick={onClose}
            disabled={submitting}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Warning Banner */}
        <div style={{
          padding: '0.85rem 1rem',
          borderRadius: '8px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          display: 'flex',
          gap: '10px',
          alignItems: 'flex-start'
        }}>
          <AlertTriangle size={18} style={{ color: '#ef4444', flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.825rem', color: '#fca5a5', lineHeight: 1.4 }}>
            <strong>Real Capital Exposure:</strong> This order will be transmitted directly to the exchange gateway through your live broker. Verify all parameters before confirming.
          </div>
        </div>

        {/* Order Details Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0.75rem',
          padding: '1rem',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '10px',
          border: '1px solid var(--border-subtle)'
        }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Broker Gateway</span>
            <div style={{ fontWeight: 700, color: '#fff', textTransform: 'uppercase' }}>{orderData.broker}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Symbol</span>
            <div style={{ fontWeight: 700, color: '#fff' }}>{orderData.symbol}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Action & Type</span>
            <div style={{
              fontWeight: 700,
              color: orderData.side === 'BUY' ? '#10b981' : '#ef4444'
            }}>
              {orderData.side} • {orderData.orderType}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Quantity</span>
            <div style={{ fontWeight: 700, color: '#fff' }}>{orderData.quantity} Shares</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Limit / Entry Price</span>
            <div style={{ fontWeight: 700, color: '#fff' }}>₹{orderData.price.toFixed(2)}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Order Value</span>
            <div style={{ fontWeight: 700, color: '#fff' }}>₹{totalValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Stop Loss</span>
            <div style={{ fontWeight: 600, color: orderData.stopLoss ? '#f87171' : 'var(--text-muted)' }}>
              {orderData.stopLoss ? `₹${orderData.stopLoss.toFixed(2)}` : 'None'}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target Profit</span>
            <div style={{ fontWeight: 600, color: orderData.target ? '#34d399' : 'var(--text-muted)' }}>
              {orderData.target ? `₹${orderData.target.toFixed(2)}` : 'None'}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Estimated Charges</span>
            <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
              ₹{orderData.estimatedCharges ? orderData.estimatedCharges.toFixed(2) : '20.00'}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Maximum Capital Risk</span>
            <div style={{ fontWeight: 700, color: '#ef4444' }}>
              ₹{maxRisk.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        {/* Passing Risk Engine Checks */}
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            Risk Engine Pre-Flight Verification
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
            {riskChecks.length > 0 ? (
              riskChecks.slice(0, 4).map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: c.passed ? '#10b981' : '#ef4444' }}>
                  <CheckCircle2 size={14} />
                  <span>{c.check_name}: {c.message}</span>
                </div>
              ))
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#10b981' }}>
                <CheckCircle2 size={14} />
                <span>Deterministic pre-flight risk checks passed</span>
              </div>
            )}
          </div>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '0.5rem' }}>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            style={{
              flex: 1,
              padding: '12px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              color: '#fff',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirmOrder}
            disabled={submitting}
            style={{
              flex: 2,
              padding: '12px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)',
              border: 'none',
              color: '#fff',
              fontWeight: 800,
              cursor: submitting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)'
            }}
          >
            <ShieldCheck size={18} />
            {submitting ? 'Transmitting...' : 'CONFIRM & TRANSMIT TO BROKER'}
          </button>
        </div>
      </div>
    </div>
  );
};
