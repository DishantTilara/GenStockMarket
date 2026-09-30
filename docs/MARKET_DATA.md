# Market Data Ingestion & Health Engine

## 1. Provider Abstraction

The platform supports multiple Indian market data providers through a standardized asynchronous interface:
- `connect()`
- `stream()`
- `get_quote(symbol)`
- `get_minute_bars(symbol, start, end)`
- `get_historical_data(symbol, start, end)`
- `get_instruments()`
- `market_status()`
- `close()`

Available implementations:
- `SimulatedMarketDataProvider`: Generates realistic live stochastic Indian stock market ticks (NIFTY 50, RELIANCE, TCS, INFY, HDFCBANK, etc.) with real volume distributions, micro-movements, and 1-minute aggregation. Ideal for development, testing, and continuous validation.
- `NSEMarketDataProvider`: Connects to authorized market feeds / APIs.

## 2. Minute Candle Ingestion & Aggregation

Candles are deduplicated and guaranteed unique via:
```sql
UNIQUE(instrument_id, interval_start)
```

Candle fields:
- `instrument_id`: UUID
- `interval_start`: TIMESTAMPTZ (floored to minute)
- `open`, `high`, `low`, `close`: NUMERIC(20, 4)
- `volume`: BIGINT
- `source_timestamp`: TIMESTAMPTZ
- `received_at`: TIMESTAMPTZ
- `is_complete`: BOOLEAN
- `quality`: VARCHAR(16) (`HIGH`, `MEDIUM`, `LOW`)
- `source`: VARCHAR(32)

## 3. Disconnect Handling & Reconciliation
When connection drops:
1. Reconnect with exponential backoff (`min_delay=1s`, `max_delay=30s`).
2. Identify missing interval window `[last_candle_time, current_time]`.
3. Fetch missing bars from provider historical endpoints.
4. Perform atomic upsert into `minute_bars`.
5. Trigger indicator recalculation and notify WebSocket clients.
