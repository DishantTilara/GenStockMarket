import React, { useRef, useEffect, useState } from 'react';

interface Candle {
  interval_start?: string;
  trade_date?: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface PriceChartProps {
  symbol: string;
  candles: Candle[];
  timeframe?: string;
  onTimeframeChange?: (tf: string) => void;
}

export const PriceChart: React.FC<PriceChartProps> = ({
  symbol,
  candles,
  timeframe = '1m',
  onTimeframeChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !candles || candles.length === 0) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Padding
    const padTop = 30;
    const padBottom = 60; // volume section
    const padRight = 65; // price axis
    const chartHeight = height - padTop - padBottom;
    const chartWidth = width - padRight;

    // Determine min/max price
    const highs = candles.map((c) => Number(c.high));
    const lows = candles.map((c) => Number(c.low));
    const maxPrice = Math.max(...highs) * 1.002;
    const minPrice = Math.min(...lows) * 0.998;
    const priceRange = maxPrice - minPrice || 1;

    // Max volume
    const volumes = candles.map((c) => Number(c.volume));
    const maxVolume = Math.max(...volumes) || 1;

    const candleCount = candles.length;
    const barWidth = Math.max(3, (chartWidth / candleCount) * 0.7);
    const spacing = chartWidth / candleCount;

    // Grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    const gridRows = 5;
    for (let i = 0; i <= gridRows; i++) {
      const y = padTop + (chartHeight / gridRows) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(chartWidth, y);
      ctx.stroke();

      // Price labels
      const p = maxPrice - (priceRange / gridRows) * i;
      ctx.fillStyle = '#64748b';
      ctx.font = '11px JetBrains Mono';
      ctx.fillText(`₹${p.toFixed(2)}`, chartWidth + 6, y + 4);
    }

    // Draw Volume Bars
    candles.forEach((c, idx) => {
      const x = idx * spacing + (spacing - barWidth) / 2;
      const volHeight = (Number(c.volume) / maxVolume) * 45;
      const y = height - 10 - volHeight;
      const isGreen = Number(c.close) >= Number(c.open);

      ctx.fillStyle = isGreen ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)';
      ctx.fillRect(x, y, barWidth, volHeight);
    });

    // Draw Candlesticks
    candles.forEach((c, idx) => {
      const open = Number(c.open);
      const close = Number(c.close);
      const high = Number(c.high);
      const low = Number(c.low);

      const x = idx * spacing + spacing / 2;
      const openY = padTop + ((maxPrice - open) / priceRange) * chartHeight;
      const closeY = padTop + ((maxPrice - close) / priceRange) * chartHeight;
      const highY = padTop + ((maxPrice - high) / priceRange) * chartHeight;
      const lowY = padTop + ((maxPrice - low) / priceRange) * chartHeight;

      const isGreen = close >= open;
      const color = isGreen ? '#10b981' : '#f43f5e';

      // Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();

      // Body
      const bodyTop = Math.min(openY, closeY);
      const bodyHeight = Math.max(2, Math.abs(closeY - openY));
      ctx.fillStyle = color;
      ctx.fillRect(x - barWidth / 2, bodyTop, barWidth, bodyHeight);
    });

    // 20-period Moving Average
    if (candles.length >= 5) {
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      let started = false;

      for (let i = 4; i < candles.length; i++) {
        const slice = candles.slice(Math.max(0, i - 19), i + 1);
        const sma = slice.reduce((acc, cur) => acc + Number(cur.close), 0) / slice.length;
        const x = i * spacing + spacing / 2;
        const y = padTop + ((maxPrice - sma) / priceRange) * chartHeight;

        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    }

    // Hover crosshair and inspection
    if (hoverIndex !== null && hoverIndex >= 0 && hoverIndex < candles.length) {
      const hX = hoverIndex * spacing + spacing / 2;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(hX, 0);
      ctx.lineTo(hX, height);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }, [candles, hoverIndex]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || candles.length === 0) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const chartWidth = rect.width - 65;
    const spacing = chartWidth / candles.length;
    const idx = Math.floor(x / spacing);
    if (idx >= 0 && idx < candles.length) {
      setHoverIndex(idx);
    }
  };

  const handleMouseLeave = () => setHoverIndex(null);

  const activeCandle = hoverIndex !== null && hoverIndex < candles.length ? candles[hoverIndex] : candles[candles.length - 1];

  return (
    <div className="card" style={{ padding: '1.25rem', position: 'relative' }}>
      {/* Chart Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>{symbol}</h3>
          {activeCandle && (
            <div style={{ display: 'flex', gap: '12px', fontSize: '0.8rem' }} className="mono">
              <span style={{ color: 'var(--text-muted)' }}>O: <b style={{ color: '#fff' }}>₹{Number(activeCandle.open).toFixed(2)}</b></span>
              <span style={{ color: 'var(--text-muted)' }}>H: <b style={{ color: 'var(--accent-green)' }}>₹{Number(activeCandle.high).toFixed(2)}</b></span>
              <span style={{ color: 'var(--text-muted)' }}>L: <b style={{ color: 'var(--accent-red)' }}>₹{Number(activeCandle.low).toFixed(2)}</b></span>
              <span style={{ color: 'var(--text-muted)' }}>C: <b style={{ color: '#fff' }}>₹{Number(activeCandle.close).toFixed(2)}</b></span>
              <span style={{ color: 'var(--text-muted)' }}>Vol: <b style={{ color: 'var(--accent-blue)' }}>{Number(activeCandle.volume).toLocaleString()}</b></span>
            </div>
          )}
        </div>

        {/* Timeframe Buttons */}
        <div style={{ display: 'flex', gap: '4px', background: 'rgba(30, 41, 59, 0.6)', padding: '3px', borderRadius: '8px' }}>
          {['1m', '5m', '15m', '1d'].map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange && onTimeframeChange(tf)}
              style={{
                background: timeframe === tf ? 'var(--accent-green)' : 'transparent',
                color: timeframe === tf ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div style={{ height: '360px', width: '100%', position: 'relative' }}>
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{ width: '100%', height: '100%', display: 'block' }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '6px' }}>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span><b style={{ color: '#10b981' }}>■</b> Bullish Candle</span>
          <span><b style={{ color: '#f43f5e' }}>■</b> Bearish Candle</span>
          <span><b style={{ color: '#f59e0b' }}>―</b> 20 EMA</span>
        </div>
        <span>Timescale: IST (UTC+5:30)</span>
      </div>
    </div>
  );
};
