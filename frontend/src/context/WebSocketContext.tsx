import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

export interface Tick {
  symbol: string;
  price: number;
  quantity?: number;
  timestamp: string;
  exchange?: string;
  provider_symbol?: string;
  change?: number;
  change_pct?: number;
  freshness?: string;
  open?: number;
  high?: number;
  low?: number;
  previous_close?: number;
  volume?: number;
}

interface WebSocketContextType {
  ticks: Record<string, Tick>;
  marketTicks: Record<string, Tick>;
  isConnected: boolean;
  lastTick: Tick | null;
  marketStatus: string;
  dataStatus: string;
  lastCandle: any | null;
}

const WebSocketContext = createContext<WebSocketContextType>({
  ticks: {},
  marketTicks: {},
  isConnected: false,
  lastTick: null,
  marketStatus: 'OPEN',
  dataStatus: 'LIVE',
  lastCandle: null,
});

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [ticks, setTicks] = useState<Record<string, Tick>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [lastTick, setLastTick] = useState<Tick | null>(null);
  const [marketStatus, setMarketStatus] = useState<string>('OPEN');
  const [dataStatus, setDataStatus] = useState<string>('LIVE');
  const [lastCandle, setLastCandle] = useState<any | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimeout: any;
    let delay = 2000;

    const connectWs = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/market`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        delay = 2000;
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'CONNECTION_ESTABLISHED') {
            if (payload.market_status) setMarketStatus(payload.market_status);
          } else if (payload.type === 'TICK' && payload.data) {
            const tick: Tick = payload.data;
            setLastTick(tick);
            if (tick.freshness) {
              setDataStatus(tick.freshness === 'FRESH' ? 'LIVE' : tick.freshness);
            }
            setTicks((prev) => ({
              ...prev,
              [tick.symbol]: tick
            }));
          } else if (payload.type === 'CANDLE_UPDATE' && payload.data) {
            setLastCandle(payload.data);
          }
        } catch {
          // ignore parsing error
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setDataStatus('DATA UNAVAILABLE');
        // Exponential reconnect with 10s cap
        reconnectTimeout = setTimeout(connectWs, delay);
        delay = Math.min(delay * 1.5, 10000);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{
      ticks,
      marketTicks: ticks,
      isConnected,
      lastTick,
      marketStatus,
      dataStatus,
      lastCandle
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useMarketStream = () => useContext(WebSocketContext);
export const useWebSocket = useMarketStream;
