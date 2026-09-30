# Architecture Overview: Indian Stock Market GenAI Platform

## 1. High-Level System Architecture

The platform is designed around strict separation of concerns, deterministic financial arithmetic, and a non-hallucinatory AI layer.

```text
                               ┌─────────────────────────────────┐
                               │   React + TypeScript Frontend   │
                               │  (Vite, SPA, Canvas/Charts, WS) │
                               └────────────────┬────────────────┘
                                                │ REST / WSS
                               ┌────────────────▼────────────────┐
                               │       FastAPI Backend API       │
                               │   (Async endpoints, JWT, RBAC)  │
                               └───────┬───────────────┬─────────┘
                                       │               │
            ┌──────────────────────────┼───────────────┴────────────────────────┐
            │                          │                                        │
            ▼                          ▼                                        ▼
┌───────────────────────┐  ┌───────────────────────┐        ┌───────────────────────────────┐
│ PostgreSQL / Timescale│  │      Redis Cache      │        │       GenAI Tool Layer        │
│ • Users & Sessions    │  │ • L1 Market Quotes    │        │ • Deterministic Tools Only    │
│ • Instruments Master  │  │ • Candlestick Buffer  │        │ • Model Abstraction (OpenAI/  │
│ • 1-Min & Daily Bars  │  │ • Pub/Sub Events      │        │   LocalLLM/Anthropic)         │
│ • Wallets & Ledgers   │  │ • Ingestion Lag stats │        │ • pgvector RAG Corpus         │
│ • Orders & Portfolios │  │ • Rate Limiting       │        └───────────────┬───────────────┘
│ • Audit Logs          │  └───────────────────────┘                        │ Structured Output
└───────────▲───────────┘                                                   ▼
            │                                               ┌───────────────────────────────┐
            ├───────────────────────────────────────────────┤          Risk Engine          │
            │                                               │ • Fund checks & Exposure limits│
┌───────────┴───────────┐                                   │ • Freshness & Volatility gates│
│   Worker Subsystem    │                                   └───────────────┬───────────────┘
│ • Market Ingestion    │                                                   │ Validated Setup
│ • 1-Min Aggregator    │                                                   ▼
│ • Gap Reconciliation  │                                   ┌───────────────────────────────┐
│ • Alert Dispatcher    │                                   │     User Approval Modal       │
│ • AI Newspaper Digest │                                   └───────────────┬───────────────┘
└───────────▲───────────┘                                                   │ Explicit Confirmation
            │                                                               ▼
┌───────────┴───────────┐                                   ┌───────────────────────────────┐
│ Market Data Provider  │                                   │        Broker Adapter         │
│ (NSE/Live/Simulated)  │                                   │ (Paper Trading / Real Broker) │
└───────────────────────┘                                   └───────────────────────────────┘
```

## 2. Key Architecture Pillars

1. **Deterministic Finance vs. Probabilistic GenAI:**
   - The LLM **never** generates prices, balances, P&L, or positions.
   - All factual queries invoke backend tools (`get_live_quote`, `get_indicators`, `get_company_fundamentals`, `analyze_portfolio`).
   - The LLM reasons over verified parameters.

2. **Continuous Market Data Pipeline:**
   - `MarketDataProvider` streams ticks / snapshots.
   - Aggregator consolidates ticks into 1-minute OHLCV candles with unique constraints `(instrument_id, interval_start)`.
   - Real-time updates push through Redis Pub/Sub to FastAPI WebSockets.

3. **Double-Entry Wallet & Ledger:**
   - Double-entry accounting design: Every balance alteration has a matching immutable `ledger_entries` record.
   - Balance separation: `available_balance` and `locked_balance`.
   - Idempotent API requests using idempotency keys.
   - PostgreSQL `NUMERIC(20, 2)` for zero floating-point error.

4. **Risk Engine & Human-In-The-Loop Execution:**
   - Live execution requires explicit user authorization.
   - Risk checks: Market open status, quote freshness (< 5s), available balance, max position size, max portfolio concentration, daily loss cutoff.

5. **Self-Healing Reconciliation Worker:**
   - Detects provider disconnects.
   - Reconnects with exponential backoff.
   - Inspects missing minute timestamps and backfills missing bars automatically.
