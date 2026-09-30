import React, { useState } from 'react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { X, ArrowDownCircle, ShieldCheck } from 'lucide-react';

interface DepositModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const DepositModal: React.FC<DepositModalProps> = ({ onClose, onSuccess }) => {
  const [amount, setAmount] = useState('25000');
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(amount);
    if (!val || val <= 0) {
      showToast('Please enter a valid deposit amount', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const idempotencyKey = `DEP-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      await ApiClient.depositFunds(val, idempotencyKey);
      showToast(`Successfully deposited ₹${val.toLocaleString('en-IN')}`, 'success');
      onSuccess();
    } catch (err: any) {
      showToast(err.message || 'Deposit failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ArrowDownCircle size={22} color="var(--accent-green)" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Add Funds to Wallet</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleDeposit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Deposit Amount (INR)
            </label>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontWeight: 600 }}>₹</span>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="input mono"
                style={{ paddingLeft: '28px', fontSize: '1.1rem', fontWeight: 600 }}
                placeholder="25000"
                min="100"
                step="100"
                required
              />
            </div>
          </div>

          {/* Quick preset pills */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '1.5rem' }}>
            {['10000', '25000', '50000', '100000'].map((preset) => (
              <button
                type="button"
                key={preset}
                onClick={() => setAmount(preset)}
                className="btn btn-secondary"
                style={{ flex: 1, padding: '6px 0', fontSize: '0.75rem', borderRadius: '6px' }}
              >
                +₹{parseInt(preset).toLocaleString('en-IN')}
              </button>
            ))}
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '12px', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <ShieldCheck size={20} color="var(--accent-green)" />
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Idempotent double-entry ledger guarantee. Funds immediately available for trading.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary" style={{ flex: 1 }}>
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ flex: 1 }}>
              {isLoading ? 'Processing...' : 'Confirm Deposit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
