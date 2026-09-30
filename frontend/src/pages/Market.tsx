import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ApiClient } from '../api/client';
import { useMarketStream } from '../context/WebSocketContext';
import { TradeExecutionModal } from '../components/TradeExecutionModal';
import { Search, Filter, Sparkles, ArrowUpRight, ArrowDownRight, Zap } from 'lucide-react';

export const Market: React.FC = () => {
  const { ticks } = useMarketStream();
  const [instruments, setInstruments] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [selectedSector, setSelectedSector] = useState('ALL');
  const [activeSetup, setActiveSetup] = useState<any>(null);
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);

  useEffect(() => {
    ApiClient.getInstruments().then(setInstruments).catch(() => {});
  }, []);

  const sectors = ['ALL', ...Array.from(new Set(instruments.map((i) => i.sector || 'General')))];

  const filtered = instruments.filter((inst) => {
    const matchSearch = inst.symbol.toLowerCase().includes(search.toLowerCase()) ||
                        inst.name.toLowerCase().includes(search.toLowerCase());
    const matchSector = selectedSector === 'ALL' || (inst.sector || 'General') === selectedSector;
    return matchSearch && matchSector;
  });

  const handleQuickSetup = async (sym: string) => {
    try {
      const setup = await ApiClient.generateTradeSetup(sym);
      setActiveSetup(setup);
      setIsTradeModalOpen(true);
    } catch {}
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>NSE Equities & Index Master</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Real-time streaming prices, volumes, and 1-click risk-checked AI setups
          </p>
        </div>

        {/* Search & Filter */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '240px' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search symbol..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input"
              style={{ paddingLeft: '32px', paddingRight: '10px', fontSize: '0.85rem' }}
            />
          </div>

          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            className="input"
            style={{ width: '160px', fontSize: '0.85rem' }}
          >
            {sectors.map((sec) => (
              <option key={sec} value={sec}>{sec}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Stocks Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Instrument</th>
              <th>Exchange</th>
              <th>Sector</th>
              <th style={{ textAlign: 'right' }}>Price (INR)</th>
              <th style={{ textAlign: 'right' }}>Volume</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((inst) => {
              const liveTick = ticks[inst.symbol];
              const p = liveTick ? liveTick.price : 1000.00;
              const vol = liveTick ? liveTick.quantity : 125000;

              return (
                <tr key={inst.id}>
                  <td>
                    <Link to={`/stock/${encodeURIComponent(inst.symbol)}`} style={{ textDecoration: 'none', color: '#fff' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{inst.symbol}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{inst.name}</div>
                    </Link>
                  </td>
                  <td>
                    <span className="badge badge-blue">{inst.exchange}</span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{inst.sector || 'Equities'}</span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div className="mono tabular-nums" style={{ fontSize: '1rem', fontWeight: 700 }}>
                      ₹{p.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className="mono tabular-nums" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {vol.toLocaleString('en-IN')}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                      <Link
                        to={`/stock/${encodeURIComponent(inst.symbol)}`}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                      >
                        Chart
                      </Link>
                      <button
                        onClick={() => handleQuickSetup(inst.symbol)}
                        className="btn btn-purple"
                        style={{ padding: '4px 10px', fontSize: '0.75rem', gap: '4px' }}
                      >
                        <Zap size={14} />
                        <span>AI Trade</span>
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {isTradeModalOpen && activeSetup && (
        <TradeExecutionModal
          setup={activeSetup}
          onClose={() => setIsTradeModalOpen(false)}
          onSuccess={() => setIsTradeModalOpen(false)}
        />
      )}
    </div>
  );
};
