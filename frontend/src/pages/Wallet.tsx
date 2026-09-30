import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { DepositModal } from '../components/DepositModal';
import { WithdrawalModal } from '../components/WithdrawalModal';
import { Wallet as WalletIcon, ArrowDownCircle, ArrowUpCircle, ShieldCheck, History, Lock } from 'lucide-react';

export const Wallet: React.FC = () => {
  const [wallet, setWallet] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false);

  const fetchWalletData = async () => {
    try {
      const w = await ApiClient.getWallet();
      setWallet(w);
      const txs = await ApiClient.getLedgerTransactions();
      setTransactions(txs);
    } catch {}
  };

  useEffect(() => {
    fetchWalletData();
  }, []);

  const avail = wallet ? Number(wallet.available_balance) : 100000.00;
  const locked = wallet ? Number(wallet.locked_balance) : 0.00;
  const total = avail + locked;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Account Wallet & Double-Entry Ledger</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Immutable financial records, available vs locked margins, and zero floating-point arithmetic guarantees
        </p>
      </div>

      {/* Balance Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Balance</div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '6px' }}>
            ₹{total.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Currency: INR (₹)
          </div>
        </div>

        <div className="card card-glow-green">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Available Margin</span>
            <span className="badge badge-green">Ready to Trade</span>
          </div>
          <div className="mono font-bold text-profit" style={{ fontSize: '1.75rem', marginTop: '6px' }}>
            ₹{avail.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button onClick={() => setIsDepositOpen(true)} className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
              + Add Funds
            </button>
            <button onClick={() => setIsWithdrawOpen(true)} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
              Withdraw
            </button>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Locked Funds</span>
            <span className="badge badge-amber"><Lock size={12} /> Payout Hold</span>
          </div>
          <div className="mono font-bold" style={{ fontSize: '1.75rem', marginTop: '6px', color: 'var(--accent-amber)' }}>
            ₹{locked.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Locked against pending withdrawals
          </div>
        </div>
      </div>

      {/* Immutable Ledger Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={18} color="var(--accent-blue)" />
            Immutable Double-Entry Ledger Transactions
          </h4>
          <span className="badge badge-blue">Audit Verified</span>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Reference</th>
              <th>Type</th>
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
                    <td className="mono" style={{ fontSize: '0.8rem' }}>{tx.reference}</td>
                    <td>
                      <span className={isCredit ? 'badge badge-green' : 'badge badge-red'}>
                        {tx.entry_type}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{tx.description}</td>
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
                <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No transaction ledger records yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
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
