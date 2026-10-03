import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ApiClient } from '../api/client';
import { Bell, Wallet as WalletIcon, ArrowUpRight, LogOut, User, Activity } from 'lucide-react';
import { DepositModal } from './DepositModal';
import { useWebSocket } from '../context/WebSocketContext';
import { ThemeSwitcher } from './ThemeSwitcher';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { dataStatus: wsDataStatus, marketStatus: wsMarketStatus } = useWebSocket();
  const [balance, setBalance] = useState<number | null>(null);
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [marketStatus, setMarketStatus] = useState<string>('OPEN');
  const [tradingMode, setTradingMode] = useState<'PAPER' | 'SANDBOX' | 'LIVE'>('PAPER');
  const currentStatus = wsMarketStatus || marketStatus;
  const activeDataStatus = wsDataStatus || (currentStatus === 'OPEN' ? 'LIVE' : 'MARKET CLOSED');

  const fetchWallet = async () => {
    try {
      const data = await ApiClient.getWallet();
      setBalance(Number(data.available_balance));
    } catch {
      setBalance(1000000.00);
    }
  };

  useEffect(() => {
    if (user) fetchWallet();
    ApiClient.getMarketStatus()
      .then((s) => setMarketStatus(s.status))
      .catch(() => setMarketStatus('OPEN'));
    ApiClient.getTradingEnvironment()
      .then((env) => setTradingMode(env.trading_mode))
      .catch(() => setTradingMode('PAPER'));
  }, [user]);

  return (
    <>
      <header style={{
        height: '64px',
        background: 'var(--nav-bg)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 2rem',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        transition: 'background 0.25s ease, border-color 0.25s ease'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <Link to="/dashboard" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, var(--primary) 0%, #1e40af 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 12px rgba(37, 99, 235, 0.4)'
            }}>
              <Activity size={20} color="#fff" />
            </div>
            <div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                GEN<span style={{ color: 'var(--primary)' }}>STOCKMARKET</span>
              </span>
            </div>
          </Link>

          {/* Environment Mode Badge */}
          <div className={
            tradingMode === 'LIVE' ? 'badge badge-rose' :
            tradingMode === 'SANDBOX' ? 'badge badge-purple' : 'paper-badge'
          } style={{
            marginLeft: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            letterSpacing: '0.04em',
            fontWeight: 700
          }}>
            <span style={{
              display: 'inline-block',
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: tradingMode === 'LIVE' ? '#ef4444' : tradingMode === 'SANDBOX' ? '#a855f7' : '#38bdf8',
              boxShadow: `0 0 8px ${tradingMode === 'LIVE' ? '#ef4444' : tradingMode === 'SANDBOX' ? '#a855f7' : '#38bdf8'}`
            }}></span>
            {tradingMode === 'LIVE' ? 'LIVE MODE' : tradingMode === 'SANDBOX' ? 'SANDBOX MODE' : 'PAPER MODE'}
          </div>

          {/* Market Status & Data Freshness Pill */}
          <div className={`badge ${currentStatus === 'OPEN' ? 'badge-green' : 'badge-amber'}`} style={{ marginLeft: '4px' }}>
            <span className={`pulsing-dot ${currentStatus === 'OPEN' ? (activeDataStatus === 'LIVE' ? 'green' : 'amber') : 'red'}`} style={{ width: '6px', height: '6px' }}></span>
            <span>NSE {currentStatus}</span>
            <span style={{ opacity: 0.7, fontSize: '0.68rem', marginLeft: '4px' }}>• {activeDataStatus}</span>
          </div>
        </div>

        {/* Right Action Items */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* Theme Switcher (White / Black) */}
          <ThemeSwitcher />

          {/* Wallet Balance Pill */}
          {user && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              background: 'var(--surface-muted)',
              border: '1px solid var(--border)',
              padding: '6px 14px',
              borderRadius: '10px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                <WalletIcon size={16} color="var(--accent-green)" />
                <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>Available</span>
              </div>
              <span className="mono tabular-nums" style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
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
              background: 'var(--surface-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              border: '1px solid var(--border)'
            }}
          >
            <Bell size={18} />
          </Link>

          {/* User Profile */}
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user.full_name}</div>
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
