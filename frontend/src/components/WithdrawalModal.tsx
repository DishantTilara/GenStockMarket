import React, { useState } from 'react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { X, ArrowUpCircle, AlertCircle } from 'lucide-react';

interface WithdrawalModalProps {
  availableBalance: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const WithdrawalModal: React.FC<WithdrawalModalProps> = ({ availableBalance, onClose, onSuccess }) => {
  const [amount, setAmount] = useState('');
  const [bankInfo, setBankInfo] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();

  const handleWithdraw = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(amount);
    if (!val || val <= 0) {
      showToast('Enter valid withdrawal amount', 'error');
      return;
    }
    if (val > availableBalance) {
      showToast('Amount exceeds available balance', 'error');
      return;
    }
    if (!bankInfo.trim()) {
      showToast('Please enter your Bank Account / IFSC details', 'error');
      return;
    }

    setIsLoading(true);
    try {
      await ApiClient.withdrawFunds(val, bankInfo);
      showToast(`Withdrawal of ₹${val.toLocaleString('en-IN')} initiated`, 'success');
      onSuccess();
    } catch (err: any) {
      showToast(err.message || 'Withdrawal failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ArrowUpCircle size={22} color="var(--accent-red)" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Request Withdrawal</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleWithdraw}>
          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Withdrawal Amount (INR)</span>
              <span className="mono" style={{ color: 'var(--text-muted)' }}>
                Available: ₹{availableBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontWeight: 600 }}>₹</span>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="input mono"
                style={{ paddingLeft: '28px', fontSize: '1.1rem', fontWeight: 600 }}
                placeholder="10000"
                max={availableBalance}
                min="100"
                step="100"
                required
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Bank Account / IFSC / UPI ID
            </label>
            <input
              type="text"
              value={bankInfo}
              onChange={(e) => setBankInfo(e.target.value)}
              className="input"
              placeholder="e.g. HDFC0001234 - 50100234567890"
              required
            />
          </div>

          <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '12px', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <AlertCircle size={20} color="var(--accent-red)" />
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Funds will transition from <b>Available</b> to <b>Locked</b> balance immediately to guarantee ledger integrity.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary" style={{ flex: 1 }}>
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="btn btn-outline-danger" style={{ flex: 1 }}>
              {isLoading ? 'Processing...' : 'Confirm Withdrawal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
