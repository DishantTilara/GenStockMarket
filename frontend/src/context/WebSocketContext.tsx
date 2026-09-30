import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

interface Tick {
  symbol: string;
  price: number;
  quantity: number;
  timestamp: string;
}

interface WebSocketContextType {
  ticks: Record<string, Tick>;
  isConnected: boolean;
  lastTick: Tick | null;
}

const WebSocketContext = createContext<WebSocketContextType>({
  ticks: {},
  isConnected: false,
  lastTick: null,
});

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [ticks, setTicks] = useState<Record<string, Tick>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [lastTick, setLastTick] = useState<Tick | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimeout: any;

    const connectWs = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/market`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'TICK' && payload.data) {
            const tick: Tick = payload.data;
            setLastTick(tick);
            setTicks((prev) => ({
              ...prev,
              [tick.symbol]: tick
            }));
          }
        } catch (e) {
          // ignore parsing error
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Exponential reconnect
        reconnectTimeout = setTimeout(connectWs, 3000);
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
    <WebSocketContext.Provider value={{ ticks, isConnected, lastTick }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useMarketStream = () => useContext(WebSocketContext);
