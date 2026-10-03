import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';

interface ThemeSwitcherProps {
  compact?: boolean;
}

export const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({ compact }) => {
  const { theme, setTheme } = useTheme();

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '3px',
        borderRadius: '20px',
        background: 'var(--surface-muted)',
        border: '1px solid var(--border)',
        gap: '2px',
        boxShadow: 'var(--shadow-sm)'
      }}
      role="group"
      aria-label="Theme selector"
    >
      <button
        type="button"
        onClick={() => setTheme('light')}
        title="Switch to White Background (Light Mode)"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          padding: compact ? '4px 8px' : '4px 11px',
          borderRadius: '16px',
          border: 'none',
          cursor: 'pointer',
          fontSize: '0.75rem',
          fontWeight: 600,
          transition: 'all 0.2s ease',
          background: theme === 'light' ? '#ffffff' : 'transparent',
          color: theme === 'light' ? '#0f172a' : 'var(--text-muted)',
          boxShadow: theme === 'light' ? '0 1px 3px rgba(0, 0, 0, 0.12)' : 'none'
        }}
      >
        <Sun size={14} color={theme === 'light' ? '#d97706' : 'currentColor'} />
        {!compact && <span>White</span>}
      </button>

      <button
        type="button"
        onClick={() => setTheme('dark')}
        title="Switch to Black Background (Dark Mode)"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          padding: compact ? '4px 8px' : '4px 11px',
          borderRadius: '16px',
          border: 'none',
          cursor: 'pointer',
          fontSize: '0.75rem',
          fontWeight: 600,
          transition: 'all 0.2s ease',
          background: theme === 'dark' ? '#1c202a' : 'transparent',
          color: theme === 'dark' ? '#f8fafc' : 'var(--text-muted)',
          boxShadow: theme === 'dark' ? '0 1px 3px rgba(0, 0, 0, 0.4)' : 'none'
        }}
      >
        <Moon size={14} color={theme === 'dark' ? '#38bdf8' : 'currentColor'} />
        {!compact && <span>Black</span>}
      </button>
    </div>
  );
};
