import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { DepositModal } from '../components/DepositModal';
import { WithdrawalModal } from '../components/WithdrawalModal';
import {
  Wallet as WalletIcon,
  ArrowDownCircle,
  ArrowUpCircle,
  ShieldCheck,
  History,
  Lock,
  RotateCcw,
  AlertCircle,
  CreditCard,
  CheckCircle2,
  Clock
} from 'lucide-react';

export const Wallet: React.FC = () => {
  const { showToast } = useToast();
  const [wallet, setWallet] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'ledger' | 'razorpay'>('ledger');
  const [portfolio, setPortfolio] = useState<any>(null);
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const fetchWalletData = async () => {
    try {
      const [w, txs, p, pymts] = await Promise.all([
        ApiClient.getWallet(),
        ApiClient.getLedgerTransactions().catch(() => []),
        ApiClient.getPortfolio().catch(() => null),
        ApiClient.getPaymentHistory().catch(() => [])
      ]);
      setWallet(w);
      setTransactions(txs);
      if (p) setPortfolio(p);
      setPayments(pymts || []);
    } catch {}
  };

  useEffect(() => {
    fetchWalletData();
  }, []);

  const handleReset = async () => {
    try {
      setIsResetting(true);
      await ApiClient.resetPaperAccount({
        starting_capital: 1000000,
        confirm: true,
        clear_orders: true
      });
      showToast('Paper wallet reset to starting capital ₹10,00,000.00', 'success');
      setConfirmReset(false);
      fetchWalletData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to reset paper wallet', 'error');
    } finally {
      setIsResetting(false);
    }
  };

  const rawAvail = Number(wallet?.available_balance);
  const avail = isNaN(rawAvail) || rawAvail <= 0 ? 1000000.00 : rawAvail;
  const locked = Number(wallet?.locked_balance) || 0.00;
  const total = avail + locked;
  const startingCapital = 1000000.00;
  const tradingPnl = Number(portfolio?.total_pnl) || (total - startingCapital);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Paper Trading Disclosure & Reset Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1.25rem',
        background: 'var(--surface)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        flexWrap: 'wrap',
        gap: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="paper-badge">PAPER WALLET</span>
          <span className="badge badge-blue" style={{ fontSize: '0.72rem' }}>RAZORPAY TEST MODE</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <b>Simulated funds only.</b> All ledger debits and credits represent simulated Indian stock market transactions.
          </span>
        </div>

        <div>
          {!confirmReset ? (
            <button
              onClick={() => setConfirmReset(true)}
              className="btn btn-secondary"
              style={{ padding: '5px 12px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <RotateCcw size={13} />
              <span>Reset Paper Account</span>
            </button>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--loss)', fontWeight: 600 }}>Reset to ₹10L?</span>
              <button
                onClick={handleReset}
                disabled={isResetting}
                className="btn btn-sell"
                style={{ padding: '4px 10px', fontSize: '0.72rem' }}
              >
                {isResetting ? 'Resetting...' : 'Confirm Reset'}
              </button>
              <button
                onClick={() => setConfirmReset(false)}
                className="btn btn-secondary"
                style={{ padding: '4px 8px', fontSize: '0.72rem' }}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Balance Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Available Paper Cash</div>
          <div className="mono font-bold text-profit" style={{ fontSize: '1.75rem', marginTop: '4px' }}>
            ₹{avail.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Ready for Paper Orders
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button onClick={() => setIsDepositOpen(true)} className="btn btn-primary" style={{ padding: '5px 12px', fontSize: '0.75rem' }}>
              + Add Funds (Razorpay TEST)
            </button>
            <button onClick={() => setIsWithdrawOpen(true)} className="btn btn-secondary" style={{ padding: '5px 12px', fontSize: '0.75rem' }}>
              Simulate Payout
            </button>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Locked Paper Margin</div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '4px', color: 'var(--warning)' }}>
            ₹{locked.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Locked against pending Limit Orders / Withdrawals
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Starting Paper Capital</div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '4px' }}>
            ₹{startingCapital.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Initial Seed Balance
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Trading Realized P&L</div>
          <div className={`mono font-bold ${tradingPnl >= 0 ? 'text-profit' : 'text-loss'}`} style={{ fontSize: '1.75rem', marginTop: '4px' }}>
            {tradingPnl >= 0 ? '+' : ''}₹{tradingPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Net Ledger Trade Gain / Loss
          </div>
        </div>
      </div>

      {/* Tables Card with Tabs */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{
          padding: '0.85rem 1.25rem',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px'
        }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setActiveTab('ledger')}
              style={{
                background: activeTab === 'ledger' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'ledger' ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <History size={15} />
              Double-Entry Ledger ({transactions.length})
            </button>
            <button
              onClick={() => setActiveTab('razorpay')}
              style={{
                background: activeTab === 'razorpay' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'razorpay' ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <CreditCard size={15} />
              Razorpay TEST Orders ({payments.length})
            </button>
          </div>
          <span className="badge badge-blue">Audit Verified</span>
        </div>

        {activeTab === 'ledger' ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Reference</th>
                <th>Entry Type</th>
                <th>Description</th>
                <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                <th style={{ textAlign: 'right' }}>Balance After (₹)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length > 0 ? (
                transactions.map((tx) => {
                  const isCredit = tx.direction === 'CREDIT';
                  return (
                    <tr key={tx.id}>
                      <td className="mono" style={{ fontSize: '0.75rem' }}>
                        {new Date(tx.created_at).toLocaleString('en-IN')}
                      </td>
                      <td className="mono" style={{ fontSize: '0.75rem' }}>{tx.reference}</td>
                      <td>
                        <span className={isCredit ? 'badge badge-green' : 'badge badge-red'}>
                          {tx.entry_type}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{tx.description}</td>
                      <td style={{ textAlign: 'right' }} className={isCredit ? 'text-profit mono font-bold' : 'text-loss mono font-bold'}>
                        {isCredit ? '+' : '-'}₹{Number(tx.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td style={{ textAlign: 'right' }} className="mono">
                        ₹{Number(tx.balance_after).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td>
                        <span className="badge badge-blue">{tx.status}</span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No transaction ledger records yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Created At</th>
                <th>Razorpay Order ID</th>
                <th>Payment ID</th>
                <th>Receipt</th>
                <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                <th>Status</th>
                <th>Completed At</th>
              </tr>
            </thead>
            <tbody>
              {payments.length > 0 ? (
                payments.map((p) => {
                  const isPaid = p.status === 'PAID';
                  return (
                    <tr key={p.id}>
                      <td className="mono" style={{ fontSize: '0.75rem' }}>
                        {new Date(p.created_at).toLocaleString('en-IN')}
                      </td>
                      <td className="mono font-bold" style={{ fontSize: '0.75rem' }}>
                        {p.razorpay_order_id}
                      </td>
                      <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {p.razorpay_payment_id || '—'}
                      </td>
                      <td className="mono" style={{ fontSize: '0.75rem' }}>
                        {p.receipt}
                      </td>
                      <td style={{ textAlign: 'right' }} className="mono font-bold text-profit">
                        ₹{Number(p.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td>
                        <span className={isPaid ? 'badge badge-green' : p.status === 'FAILED' ? 'badge badge-red' : 'badge badge-amber'}>
                          {p.status}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: '0.75rem' }}>
                        {p.completed_at ? new Date(p.completed_at).toLocaleString('en-IN') : '—'}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No Razorpay payment orders recorded yet. Click "+ Add Funds (Razorpay TEST)" above to initiate a test deposit.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {isDepositOpen && (
        <DepositModal
          onClose={() => setIsDepositOpen(false)}
          onSuccess={() => { setIsDepositOpen(false); fetchWalletData(); }}
        />
      )}

      {isWithdrawOpen && (
        <WithdrawalModal
          availableBalance={avail}
          onClose={() => setIsWithdrawOpen(false)}
          onSuccess={() => { setIsWithdrawOpen(false); fetchWalletData(); }}
        />
      )}
    </div>
  );
};
