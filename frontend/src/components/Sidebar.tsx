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
  Layers,
  BarChart3,
  Wallet,
  Settings,
  ShieldCheck,
  Server,
  Bot
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/market', label: 'Markets', icon: TrendingUp },
  { path: '/watchlists', label: 'Watchlist', icon: ListOrdered },
  { path: '/orders', label: 'Orders', icon: Layers, badge: 'Live' },
  { path: '/positions', label: 'Positions', icon: BarChart3 },
  { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { path: '/scanner', label: 'Screener', icon: Scan },
  { path: '/strategies', label: 'Strategies', icon: Sliders },
  { path: '/backtests', label: 'Backtests', icon: History },
  { path: '/ai', label: 'GenAI Analyst', icon: Sparkles, badge: 'AI' },
  { path: '/ai/auto-trading', label: 'AI Auto-Trading', icon: Bot, badge: 'Auto' },
  { path: '/ai/newspaper', label: 'News', icon: Newspaper },
  { path: '/wallet', label: 'Paper Wallet', icon: Wallet },
  { path: '/risk', label: 'Risk Controls', icon: ShieldCheck, badge: 'Guard' },
  { path: '/broker', label: 'Broker Gateway', icon: Server, badge: 'API' },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside style={{
      width: '240px',
      background: 'var(--sidebar-bg)',
      backdropFilter: 'blur(16px)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.25rem 0.75rem',
      gap: '4px',
      transition: 'background 0.25s ease, border-color 0.25s ease'
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
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                background: isActive ? 'var(--surface-muted)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
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
      <div style={{ marginTop: 'auto', padding: '0.75rem', background: 'var(--surface-muted)', borderRadius: '10px', border: '1px solid var(--border)' }}>
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
