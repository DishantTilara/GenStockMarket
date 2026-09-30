import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  ListOrdered,
  Scan,
  Bell,
  Sparkles,
  Newspaper,
  Sliders,
  History,
  Briefcase,
  Wallet,
  Settings,
  ShieldCheck
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/market', label: 'Market Overview', icon: TrendingUp },
  { path: '/watchlists', label: 'Watchlists', icon: ListOrdered },
  { path: '/scanner', label: 'Market Scanner', icon: Scan },
  { path: '/alerts', label: 'Alerts', icon: Bell },
  { path: '/ai', label: 'GenAI Analyst', icon: Sparkles, badge: 'AI' },
  { path: '/ai/newspaper', label: 'AI Newspaper', icon: Newspaper, badge: 'Daily' },
  { path: '/strategies', label: 'Strategy Engine', icon: Sliders },
  { path: '/backtests', label: 'Backtesting', icon: History },
  { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { path: '/wallet', label: 'Wallet & Ledger', icon: Wallet },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside style={{
      width: '240px',
      background: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(16px)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.25rem 0.75rem',
      gap: '4px'
    }}>
      <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 0.75rem 0.5rem' }}>
        Platform Menu
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.65rem 0.85rem',
                borderRadius: '8px',
                textDecoration: 'none',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                background: isActive ? 'linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--accent-green)' : '3px solid transparent',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 500,
                transition: 'all 0.15s ease'
              })}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Icon size={18} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={item.badge === 'AI' ? 'badge badge-purple' : 'badge badge-blue'} style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Safety Badge */}
      <div style={{ marginTop: 'auto', padding: '0.75rem', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-green)', fontSize: '0.75rem', fontWeight: 600 }}>
          <ShieldCheck size={16} />
          <span>Risk Shield Active</span>
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Human-in-the-loop validation & 6-point pre-trade checks enabled.
        </div>
      </div>
    </aside>
  );
};
