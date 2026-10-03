import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ListOrdered,
  Layers,
  Briefcase,
  Wallet
} from 'lucide-react';

export const MobileNav: React.FC = () => {
  return (
    <nav className="mobile-bottom-nav">
      <NavLink
        to="/dashboard"
        className={({ isActive }) => `mobile-nav-item ${isActive ? 'active' : ''}`}
      >
        <LayoutDashboard size={20} />
        <span>Home</span>
      </NavLink>

      <NavLink
        to="/watchlists"
        className={({ isActive }) => `mobile-nav-item ${isActive ? 'active' : ''}`}
      >
        <ListOrdered size={20} />
        <span>Watchlist</span>
      </NavLink>

      <NavLink
        to="/orders"
        className={({ isActive }) => `mobile-nav-item ${isActive ? 'active' : ''}`}
      >
        <Layers size={20} />
        <span>Orders</span>
      </NavLink>

      <NavLink
        to="/positions"
        className={({ isActive }) => `mobile-nav-item ${isActive ? 'active' : ''}`}
      >
        <Briefcase size={20} />
        <span>Positions</span>
      </NavLink>

      <NavLink
        to="/wallet"
        className={({ isActive }) => `mobile-nav-item ${isActive ? 'active' : ''}`}
      >
        <Wallet size={20} />
        <span>Wallet</span>
      </NavLink>
    </nav>
  );
};
