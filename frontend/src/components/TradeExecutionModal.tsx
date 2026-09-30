import React, { useState } from 'react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { ShieldCheck, AlertTriangle, CheckCircle2, X, Lock } from 'lucide-react';

interface TradeExecutionModalProps {
  setup: any;
  onClose: () => void;
  onSuccess: (order: any) => void;
}

export const TradeExecutionModal: React.FC<TradeExecutionModalProps> = ({ setup, onClose, onSuccess }) => {
  const [step, setStep] = useState<'VALIDATING' | 'READY_FOR_APPROVAL' | 'REJECTED' | 'EXECUTING'>('VALIDATING');
  const [riskData, setRiskData] = useState<any>(null);
  const { showToast } = useToast();

  React.useEffect(() => {
    // Run pre-flight risk checks immediately upon opening
    const checkRisk = async () => {
      try {
        const payload = {
          symbol: setup.symbol,
          side: setup.side,
          order_type: 'LIMIT',
          quantity: setup.quantity,
          price: setup.entry_zone ? (setup.entry_zone.min + setup.entry_zone.max) / 2 : setup.stop_loss * 1.02,
          stop_loss: setup.stop_loss,
          target: setup.target_price
        };
        const res = await ApiClient.validateRisk(payload);
        setRiskData(res);
        if (res.approved) {
          setStep('READY_FOR_APPROVAL');
        } else {
          setStep('REJECTED');
        }
      } catch (err: any) {
        showToast(err.message || 'Risk validation failed', 'error');
        setStep('REJECTED');
      }
    };

    checkRisk();
  }, [setup]);

  const handleConfirmOrder = async () => {
    if (!riskData?.confirmation_token) return;
    setStep('EXECUTING');
    try {
      const execPayload = {
        confirmation_token: riskData.confirmation_token,
        symbol: setup.symbol,
        side: setup.side,
        order_type: 'LIMIT',
        quantity: setup.quantity,
        price: setup.entry_zone ? (setup.entry_zone.min + setup.entry_zone.max) / 2 : setup.stop_loss * 1.02,
        stop_loss: setup.stop_loss,
        target: setup.target_price
      };
      const order = await ApiClient.executeOrder(execPayload);
      showToast(`Order executed: ${order.side} ${order.quantity} ${order.symbol} (${order.broker_order_id})`, 'success');
      onSuccess(order);
    } catch (err: any) {
      showToast(err.message || 'Order execution failed', 'error');
      setStep('READY_FOR_APPROVAL');
    }
  };

  const isBuy = setup.side === 'BUY';

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '580px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={22} color="var(--accent-green)" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Pre-Trade Risk Engine & User Confirmation</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Trade Details Summary */}
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '14px', borderRadius: '10px', marginBottom: '1.25rem', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem', fontWeight: 700 }}>{setup.symbol}</span>
              <span className={`badge ${isBuy ? 'badge-green' : 'badge-red'}`} style={{ fontSize: '0.8rem' }}>
                {setup.side}
              </span>
            </div>
            <div className="mono" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Qty: <b style={{ color: '#fff' }}>{setup.quantity}</b>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', fontSize: '0.8rem' }} className="mono">
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Entry Zone:</span>
              <div style={{ color: '#fff', fontWeight: 600 }}>₹{setup.entry_zone ? `${setup.entry_zone.min} - ${setup.entry_zone.max}` : 'Market'}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Stop Loss:</span>
              <div style={{ color: 'var(--accent-red)', fontWeight: 600 }}>₹{Number(setup.stop_loss).toFixed(2)}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Target:</span>
              <div style={{ color: 'var(--accent-green)', fontWeight: 600 }}>₹{Number(setup.target_price).toFixed(2)}</div>
            </div>
          </div>
        </div>

        {/* Risk Check Inspection List */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Automated Risk Gate Checks
          </div>
          {riskData?.checks ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {riskData.checks.map((chk: any, idx: number) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: chk.passed ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.1)',
                    border: `1px solid ${chk.passed ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.3)'}`
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
                    {chk.passed ? <CheckCircle2 size={16} color="var(--accent-green)" /> : <AlertTriangle size={16} color="var(--accent-red)" />}
                    <span style={{ color: chk.passed ? '#fff' : 'var(--accent-red)', fontWeight: 500 }}>{chk.check_name}</span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{chk.message}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Running pre-trade risk validations...
            </div>
          )}
        </div>

        {/* Explicit Human Confirmation Action */}
        {step === 'READY_FOR_APPROVAL' && (
          <div style={{ display: 'flex', gap: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary" style={{ flex: 1 }}>
              Reject / Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmOrder}
              className={`btn ${isBuy ? 'btn-primary' : 'btn-outline-danger'}`}
              style={{ flex: 1.5, gap: '8px' }}
            >
              <Lock size={16} />
              <span>Confirm & Execute {setup.side}</span>
            </button>
          </div>
        )}

        {step === 'REJECTED' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ padding: '12px', background: 'rgba(244, 63, 94, 0.15)', borderRadius: '8px', color: 'var(--accent-red)', fontSize: '0.85rem' }}>
              <b>Order Blocked by Risk Engine:</b> {riskData?.rejection_reason || 'Safety limits breached.'}
            </div>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Close
            </button>
          </div>
        )}

        {step === 'EXECUTING' && (
          <div style={{ textAlign: 'center', padding: '12px', color: 'var(--text-secondary)' }}>
            Submitting user-approved order to broker gateway...
          </div>
        )}
      </div>
    </div>
  );
};
