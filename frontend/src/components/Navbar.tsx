import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ApiClient } from '../api/client';
import { Bell, Wallet as WalletIcon, ArrowUpRight, LogOut, User, Activity } from 'lucide-react';
import { DepositModal } from './DepositModal';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [balance, setBalance] = useState<number | null>(null);
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [marketStatus, setMarketStatus] = useState<string>('OPEN');

  const fetchWallet = async () => {
    try {
      const data = await ApiClient.getWallet();
      setBalance(Number(data.available_balance));
    } catch {
      setBalance(100000.00);
    }
  };

  useEffect(() => {
    if (user) fetchWallet();
    ApiClient.getMarketStatus()
      .then((s) => setMarketStatus(s.status))
      .catch(() => setMarketStatus('OPEN'));
  }, [user]);

  return (
    <>
      <header style={{
        height: '64px',
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 2rem',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <Link to="/dashboard" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #10b981 0%, #38bdf8 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(16, 185, 129, 0.4)'
            }}>
              <Activity size={20} color="#fff" />
            </div>
            <div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
                DALAL STREET <span style={{ color: 'var(--accent-green)' }}>AI</span>
              </span>
            </div>
          </Link>

          {/* Market Status Pill */}
          <div className={`badge ${marketStatus === 'OPEN' ? 'badge-green' : 'badge-amber'}`} style={{ marginLeft: '12px' }}>
            <span className={`pulsing-dot ${marketStatus === 'OPEN' ? 'green' : 'red'}`} style={{ width: '6px', height: '6px' }}></span>
            <span>NSE {marketStatus}</span>
          </div>
        </div>

        {/* Right Action Items */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Wallet Balance Pill */}
          {user && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid var(--border-subtle)',
              padding: '6px 14px',
              borderRadius: '10px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                <WalletIcon size={16} color="var(--accent-green)" />
                <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>Available</span>
              </div>
              <span className="mono tabular-nums" style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fff' }}>
                ₹{balance !== null ? balance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '1,00,000.00'}
              </span>
              <button
                onClick={() => setIsDepositOpen(true)}
                className="btn btn-primary"
                style={{ padding: '4px 10px', fontSize: '0.75rem', borderRadius: '6px' }}
              >
                + Add Funds
              </button>
            </div>
          )}

          {/* Notifications */}
          <Link
            to="/alerts"
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              background: 'rgba(30, 41, 59, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              border: '1px solid var(--border-subtle)'
            }}
          >
            <Bell size={18} />
          </Link>

          {/* User Profile */}
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>{user.full_name}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{user.role}</div>
              </div>
              <button
                onClick={() => { logout(); navigate('/login'); }}
                title="Logout"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '6px'
                }}
              >
                <LogOut size={18} />
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn btn-primary">Sign In</Link>
          )}
        </div>
      </header>

      {isDepositOpen && (
        <DepositModal
          onClose={() => setIsDepositOpen(false)}
          onSuccess={() => { setIsDepositOpen(false); fetchWallet(); }}
        />
      )}
    </>
  );
};
