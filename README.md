# Indian Stock Market GenAI Platform

A modular, production-ready full-stack market intelligence and quantitative trading platform for Indian equities (NSE/BSE). Built with FastAPI, PostgreSQL/TimescaleDB, Redis, React, TypeScript, and a tool-grounded GenAI engine.

---

## 🌟 Key Features

- **Continuous Market Data Ingestion**: Real-time tick & snapshot streaming, 1-minute OHLCV candle aggregation, disconnect recovery, and gap reconciliation.
- **Market Health & Observability**: Real-time health metrics (`/health/market`, `/health/database`, `/health/redis`), ingestion lag tracking, symbol counts, and reconnect monitors.
- **Double-Entry Wallet & Immutable Ledger**: Strict `available_balance` / `locked_balance` enforcement, PostgreSQL `NUMERIC(20,2)`, idempotent deposits and withdrawals.
- **Deterministic Technical Analysis**: Modular `indicator_service` providing SMA, EMA, RSI, MACD, Bollinger Bands, ATR, VWAP, Support/Resistance, and Trend detection.
- **Market Scanner**: Flexible scanner rules engine supporting EMA crossovers, RSI extremes, VWAP breakouts, volume spikes, and natural language to scanner translation.
- **RAG & GenAI Analyst**: PostgreSQL + `pgvector` semantic retrieval for filings, news, and reports. Multi-provider LLM abstraction (OpenAI, Local Ollama, Anthropic) using internal tools only (zero price hallucinations).
- **AI Market Newspaper**: Automated Pre-Market, Intraday, and Closing intelligence briefings compiled from live market feeds.
- **Backtesting & Strategy Engine**: Walk-forward historical testing with slippage, brokerage, STT/taxes, Sharpe ratio, Max Drawdown, and equity curves.
- **Risk Engine & Broker Gateway**: Multi-tier pre-trade risk checks (quote freshness, max order value, sector concentration, daily loss limit) and explicit human approval modal prior to execution.
- **Realtime WebSocket Streaming**: Live prices, candle completion notifications, alert triggers, and wallet balance updates.

---

## 🏗️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, React Router, Canvas/Candlestick Charts, WebSocket Client, Modern Glassmorphism CSS |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic |
| **Database** | PostgreSQL 16 + TimescaleDB (Time-series) + pgvector (RAG) |
| **Cache & Pub/Sub** | Redis 7 |
| **Workers** | Asyncio Background Workers (Market Ingestion, Reconciliation, Alerts, AI Newspaper) |
| **AI Layer** | Tool-Grounded LLM Provider Abstraction (OpenAI / Ollama Local / Anthropic) |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

---

## 🚀 Quick Start with Docker

```bash
# 1. Clone repository
git clone https://github.com/your-username/indian-stock-genai.git
cd indian-stock-genai

# 2. Configure environment
cp .env.example .env

# 3. Start full stack (PostgreSQL, Redis, Backend, Workers, Frontend)
docker compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Market Health**: [http://localhost:8000/health/market](http://localhost:8000/health/market)

---

## 💻 Standalone Local Development

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
python -m app.main
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🔒 Security & Compliance Notice

This platform is configured for educational, paper trading, and analytical purposes. Real broker execution requires explicit user authorization, valid exchange-approved data vendor licenses, broker API terms adherence, and regulatory compliance (SEBI regulations where applicable).
