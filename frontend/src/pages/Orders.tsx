import React, { useState, useEffect } from 'react';
import { ApiClient } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../context/WebSocketContext';
import { 
  FileText, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  RefreshCw, 
  Filter, 
  Edit3, 
  Trash2, 
  Info,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

interface OrderItem {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  order_type: string;
  quantity: number;
  price: number;
  execution_price?: number;
  stop_loss?: number;
  target?: number;
  status: string;
  charges?: number;
  realized_pnl?: number;
  error_message?: string;
  broker_order_id?: string;
  created_at: string;
}

export const Orders: React.FC = () => {
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'ALL' | 'OPEN' | 'FILLED' | 'CANCELLED' | 'REJECTED'>('ALL');
  const [selectedOrder, setSelectedOrder] = useState<OrderItem | null>(null);
  const [orderEvents, setOrderEvents] = useState<any[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [modifyModalOpen, setModifyModalOpen] = useState(false);
  const [modifyingOrder, setModifyingOrder] = useState<OrderItem | null>(null);
  const [modQty, setModQty] = useState(1);
  const [modPrice, setModPrice] = useState(0);
  const [modSl, setModSl] = useState<number | undefined>();
  const [modTarget, setModTarget] = useState<number | undefined>();

  const { showToast } = useToast();
  const { isConnected } = useWebSocket();

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getOrders(activeTab);
      setOrders(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch orders', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [activeTab]);

  const handleCancelOrder = async (orderId: string) => {
    if (!window.confirm('Are you sure you want to cancel this pending paper order?')) return;
    try {
      await ApiClient.cancelOrder(orderId);
      showToast('Paper order cancelled successfully', 'info');
      fetchOrders();
    } catch (err: any) {
      showToast(err.message || 'Failed to cancel order', 'error');
    }
  };

  const handleViewEvents = async (order: OrderItem) => {
    setSelectedOrder(order);
    try {
      setEventsLoading(true);
      const events = await ApiClient.getOrderEvents(order.id);
      setOrderEvents(events);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch order events', 'error');
    } finally {
      setEventsLoading(false);
    }
  };

  const openModifyModal = (order: OrderItem) => {
    setModifyingOrder(order);
    setModQty(order.quantity);
    setModPrice(order.price);
    setModSl(order.stop_loss);
    setModTarget(order.target);
    setModifyModalOpen(true);
  };

  const submitModify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modifyingOrder) return;
    try {
      await ApiClient.modifyOrder(modifyingOrder.id, {
        quantity: modQty,
        price: modPrice,
        stop_loss: modSl,
        target_price: modTarget
      });
      showToast('Order modified successfully', 'success');
      setModifyModalOpen(false);
      fetchOrders();
    } catch (err: any) {
      showToast(err.message || 'Failed to modify order', 'error');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'FILLED':
        return <span className="badge badge-green"><CheckCircle2 size={12} /> FILLED</span>;
      case 'PENDING':
      case 'SUBMITTED':
        return <span className="badge badge-amber"><Clock size={12} /> PENDING</span>;
      case 'CANCELLED':
        return <span className="badge badge-red"><XCircle size={12} /> CANCELLED</span>;
      case 'REJECTED':
        return <span className="badge badge-red"><AlertCircle size={12} /> REJECTED</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Orders</h1>
            <span className="paper-badge">PAPER TRADING • SIMULATED FUNDS</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Authoritative paper order book and execution audit trail
          </p>
        </div>

        <button 
          onClick={fetchOrders} 
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '0.45rem 0.85rem' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        {(['ALL', 'OPEN', 'FILLED', 'CANCELLED', 'REJECTED'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '0.45rem 1rem',
              fontSize: '0.825rem',
              fontWeight: 600,
              background: activeTab === tab ? 'var(--surface-muted)' : 'transparent',
              color: activeTab === tab ? 'var(--primary)' : 'var(--text-secondary)',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {tab === 'ALL' ? 'All Orders' : tab.charAt(0) + tab.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Orders Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Order Price</th>
                <th>Exec Price</th>
                <th>Charges</th>
                <th>P&L</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    Loading paper orders...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No orders found in <strong>{activeTab}</strong> tab.
                  </td>
                </tr>
              ) : (
                orders.map(order => (
                  <tr key={order.id}>
                    <td className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {new Date(order.created_at).toLocaleTimeString('en-IN', { hour12: false })}
                    </td>
                    <td>
                      <span style={{ fontWeight: 700 }}>{order.symbol}</span>
                    </td>
                    <td>
                      <span className={`badge ${order.side === 'BUY' ? 'badge-green' : 'badge-red'}`}>
                        {order.side}
                      </span>
                    </td>
                    <td className="mono" style={{ fontSize: '0.8rem' }}>{order.order_type}</td>
                    <td className="mono tabular-nums">{order.quantity}</td>
                    <td className="mono tabular-nums">₹{Number(order.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="mono tabular-nums">
                      {order.execution_price ? `₹${Number(order.execution_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="mono tabular-nums" style={{ color: 'var(--text-muted)' }}>
                      ₹{Number(order.charges || 0).toFixed(2)}
                    </td>
                    <td className="mono tabular-nums">
                      {order.realized_pnl !== undefined && order.realized_pnl !== null ? (
                        <span className={order.realized_pnl >= 0 ? 'text-profit' : 'text-loss'} style={{ fontWeight: 600 }}>
                          {order.realized_pnl >= 0 ? '+' : ''}₹{Number(order.realized_pnl).toFixed(2)}
                        </span>
                      ) : '—'}
                    </td>
                    <td>{getStatusBadge(order.status)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem' }}>
                        {order.status === 'PENDING' && (
                          <>
                            <button
                              onClick={() => openModifyModal(order)}
                              title="Modify Order"
                              className="btn btn-secondary"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            >
                              <Edit3 size={13} />
                            </button>
                            <button
                              onClick={() => handleCancelOrder(order.id)}
                              title="Cancel Order"
                              className="btn btn-outline-danger"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            >
                              <Trash2 size={13} />
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleViewEvents(order)}
                          title="View Audit Events"
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        >
                          <Info size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Events Modal */}
      {selectedOrder && (
        <div className="modal-overlay" onClick={() => setSelectedOrder(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '540px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Order Audit Lifecycle</h3>
                <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  ID: {selectedOrder.id}
                </span>
              </div>
              <button 
                onClick={() => setSelectedOrder(null)} 
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.25rem' }}
              >
                &times;
              </button>
            </div>

            <div style={{ background: 'var(--surface-muted)', borderRadius: '8px', padding: '0.75rem', marginBottom: '1rem', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Symbol</div>
                <div style={{ fontWeight: 700 }}>{selectedOrder.symbol}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Side / Type</div>
                <div style={{ fontWeight: 700 }}>{selectedOrder.side} {selectedOrder.order_type}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Quantity</div>
                <div className="mono" style={{ fontWeight: 700 }}>{selectedOrder.quantity}</div>
              </div>
            </div>

            <h4 style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              Lifecycle Events
            </h4>

            {eventsLoading ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>Loading events...</div>
            ) : orderEvents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>No audit events found.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '250px', overflowY: 'auto' }}>
                {orderEvents.map((evt, idx) => (
                  <div 
                    key={evt.id || idx}
                    style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      padding: '0.6rem 0.8rem', 
                      background: 'var(--surface-muted)', 
                      borderRadius: '6px',
                      fontSize: '0.8rem'
                    }}
                  >
                    <div>
                      <span className="badge badge-blue" style={{ marginRight: '0.5rem' }}>{evt.event_type}</span>
                      {evt.details && (
                        <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {JSON.stringify(evt.details).substring(0, 50)}...
                        </span>
                      )}
                    </div>
                    <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(evt.created_at).toLocaleTimeString('en-IN', { hour12: false })}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setSelectedOrder(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modify Order Modal */}
      {modifyModalOpen && modifyingOrder && (
        <div className="modal-overlay" onClick={() => setModifyModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '420px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
              Modify Pending Order ({modifyingOrder.symbol})
            </h3>
            <form onSubmit={submitModify} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Quantity
                </label>
                <input 
                  type="number" 
                  min="1" 
                  value={modQty} 
                  onChange={e => setModQty(parseInt(e.target.value) || 1)} 
                  className="input" 
                  required 
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Limit Price (₹)
                </label>
                <input 
                  type="number" 
                  step="0.05" 
                  value={modPrice} 
                  onChange={e => setModPrice(parseFloat(e.target.value) || 0)} 
                  className="input" 
                  required 
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Stop Loss (Optional)
                </label>
                <input 
                  type="number" 
                  step="0.05" 
                  value={modSl || ''} 
                  onChange={e => setModSl(e.target.value ? parseFloat(e.target.value) : undefined)} 
                  className="input" 
                  placeholder="e.g. 2900.00" 
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                  Target (Optional)
                </label>
                <input 
                  type="number" 
                  step="0.05" 
                  value={modTarget || ''} 
                  onChange={e => setModTarget(e.target.value ? parseFloat(e.target.value) : undefined)} 
                  className="input" 
                  placeholder="e.g. 3150.00" 
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setModifyModalOpen(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Update Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;
