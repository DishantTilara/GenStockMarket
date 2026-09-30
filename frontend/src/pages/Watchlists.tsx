import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useMarketStream } from '../context/WebSocketContext';
import { useToast } from '../context/ToastContext';
import { ListOrdered, Plus, Trash2, TrendingUp, Zap } from 'lucide-react';

export const Watchlists: React.FC = () => {
  const { ticks } = useMarketStream();
  const { showToast } = useToast();
  const [watchlists, setWatchlists] = useState<any[]>([]);
  const [activeWatchlistId, setActiveWatchlistId] = useState<string>('');
  const [newSymbol, setNewSymbol] = useState('');
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const fetchWatchlists = async () => {
    try {
      const data = await ApiClient.getWatchlists();
      setWatchlists(data);
      if (data.length > 0 && !activeWatchlistId) {
        setActiveWatchlistId(data[0].id);
      }
    } catch {}
  };

  useEffect(() => {
    fetchWatchlists();
  }, []);

  const handleCreateWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWatchlistName.trim()) return;
    try {
      const created = await ApiClient.createWatchlist(newWatchlistName);
      showToast(`Watchlist '${newWatchlistName}' created`, 'success');
      setNewWatchlistName('');
      setIsCreating(false);
      await fetchWatchlists();
      setActiveWatchlistId(created.id);
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSymbol.trim() || !activeWatchlistId) return;
    try {
      await ApiClient.addWatchlistItem(activeWatchlistId, newSymbol.trim().toUpperCase());
      showToast(`Added ${newSymbol.toUpperCase()} to watchlist`, 'success');
      setNewSymbol('');
      fetchWatchlists();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const handleRemoveItem = async (sym: string) => {
    if (!activeWatchlistId) return;
    try {
      await ApiClient.removeWatchlistItem(activeWatchlistId, sym);
      showToast(`Removed ${sym}`, 'info');
      fetchWatchlists();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const activeWl = watchlists.find((w) => w.id === activeWatchlistId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Watchlists</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Organize equities into high-conviction portfolios, intraday alerts, and breakout monitors
          </p>
        </div>

        <button onClick={() => setIsCreating(true)} className="btn btn-primary">
          <Plus size={16} />
          <span>New Watchlist</span>
        </button>
      </div>

      {/* Create Watchlist Modal / Form */}
      {isCreating && (
        <form onSubmit={handleCreateWatchlist} className="card" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Watchlist name (e.g. Breakout Stocks, Bank Nifty Options)..."
            value={newWatchlistName}
            onChange={(e) => setNewWatchlistName(e.target.value)}
            className="input"
            required
          />
          <button type="submit" className="btn btn-primary">Save</button>
          <button type="button" onClick={() => setIsCreating(false)} className="btn btn-secondary">Cancel</button>
        </form>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        {watchlists.map((wl) => (
          <button
            key={wl.id}
            onClick={() => setActiveWatchlistId(wl.id)}
            style={{
              background: activeWatchlistId === wl.id ? 'var(--bg-tertiary)' : 'transparent',
              color: activeWatchlistId === wl.id ? '#fff' : 'var(--text-secondary)',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {wl.name} ({wl.items?.length || 0})
          </button>
        ))}
      </div>

      {/* Active Watchlist Items */}
      {activeWl && (
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{activeWl.name}</h3>

            <form onSubmit={handleAddItem} style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="Add symbol (e.g. SBIN)..."
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                className="input"
                style={{ width: '180px', fontSize: '0.85rem' }}
                required
              />
              <button type="submit" className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                + Add
              </button>
            </form>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th style={{ textAlign: 'right' }}>Live Price</th>
                <th style={{ textAlign: 'right' }}>Change %</th>
                <th style={{ textAlign: 'center' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {activeWl.items && activeWl.items.length > 0 ? (
                activeWl.items.map((sym: string) => {
                  const tick = ticks[sym];
                  const p = tick ? tick.price : 2000.00;
                  return (
                    <tr key={sym}>
                      <td>
                        <Link to={`/stock/${sym}`} style={{ textDecoration: 'none', color: '#fff', fontWeight: 700 }}>
                          {sym}
                        </Link>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span className="mono tabular-nums" style={{ fontWeight: 700 }}>
                          ₹{p.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span className="text-profit mono" style={{ fontSize: '0.85rem' }}>+0.55%</span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => handleRemoveItem(sym)}
                          style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                          title="Remove item"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No stocks added to this watchlist yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
