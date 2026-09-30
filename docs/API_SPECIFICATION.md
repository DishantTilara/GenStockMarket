# API Specification (v1)

All production endpoints are prefixed with `/api/v1`.

## Authentication & Users
- `POST /api/v1/auth/register` - Create user account
- `POST /api/v1/auth/login` - Login with credentials (returns JWT access & refresh tokens)
- `POST /api/v1/auth/refresh` - Refresh access token with rotation
- `POST /api/v1/auth/logout` - Invalidate current session
- `POST /api/v1/auth/forgot-password` - Request password reset token
- `POST /api/v1/auth/reset-password` - Reset password with token
- `GET /api/v1/auth/me` - Current user profile & roles

## Wallet & Ledger
- `GET /api/v1/wallet` - Current wallet balance (`available_balance`, `locked_balance`)
- `POST /api/v1/wallet/deposit` - Deposit funds (simulated/payment intent with idempotency key)
- `POST /api/v1/wallet/withdraw` - Initiate withdrawal (locks funds, validates balance)
- `GET /api/v1/wallet/transactions` - Paginated immutable ledger entries
- `GET /api/v1/wallet/deposits` - Deposit requests history
- `GET /api/v1/wallet/withdrawals` - Withdrawal requests history

## Market Data
- `GET /api/v1/market/status` - Current exchange market status (open, closed, pre-open)
- `GET /api/v1/market/instruments` - Master list of traded Indian equities & indices
- `GET /api/v1/market/quote/{symbol}` - Latest quote snapshot (L1, OHLC, volume)
- `GET /api/v1/market/minute/{symbol}` - 1-minute historical candlestick bars
- `GET /api/v1/market/history/{symbol}` - Daily/historical time series bars

## Technical Indicators
- `GET /api/v1/technical/{symbol}` - Compute indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, VWAP, Support/Resistance)

## Scanner & Watchlists
- `GET /api/v1/scanner/presets` - Predefined scanner conditions (Volume Breakout, 52W High, RSI Oversold, etc.)
- `POST /api/v1/scanner/run` - Execute scanner rules on universe of stocks
- `POST /api/v1/scanner/nl-query` - AI translation of natural language query into structured rules
- `GET /api/v1/watchlists` - User watchlists
- `POST /api/v1/watchlists` - Create watchlist
- `POST /api/v1/watchlists/{id}/items` - Add symbol to watchlist
- `DELETE /api/v1/watchlists/{id}/items/{symbol}` - Remove symbol from watchlist

## Alerts
- `GET /api/v1/alerts` - List active user alerts
- `POST /api/v1/alerts` - Create alert (Price, RSI, Volume, Breakout)
- `DELETE /api/v1/alerts/{id}` - Delete alert
- `GET /api/v1/alerts/history` - Triggered alert events log

## News & Corporate Filings
- `GET /api/v1/news` - Filtered news feed with verified sentiment tags
- `GET /api/v1/news/announcements` - Corporate filings & exchange announcements

## GenAI Assistant & Newspaper
- `POST /api/v1/ai/chat` - Conversational interface backed by internal tool execution
- `GET /api/v1/ai/stock/{symbol}` - Structured AI stock intelligence report
- `GET /api/v1/ai/newspaper` - Morning pre-market, intraday, and closing market digests

## Strategies & Backtests
- `GET /api/v1/strategies` - List user strategies
- `POST /api/v1/strategies` - Save custom strategy
- `POST /api/v1/strategies/nl-generate` - Convert natural language to backtestable rules
- `POST /api/v1/backtests/run` - Execute simulated backtest with slippage and STT/brokerage
- `GET /api/v1/backtests/{id}` - Retrieve backtest results, trades, and equity curve

## Portfolio & Orders
- `GET /api/v1/portfolio` - Holdings, sector allocation, unrealized/realized P&L
- `POST /api/v1/orders/trade-setup` - Generate structured trade setup
- `POST /api/v1/orders/validate-risk` - Run pre-trade risk engine validation
- `POST /api/v1/orders/execute` - Execute user-approved live/paper order

## Health & Observability
- `GET /health` - System overview
- `GET /health/database` - PostgreSQL connection & latency
- `GET /health/redis` - Redis ping & memory usage
- `GET /health/market` - Market ingestion lag, symbols tracked, missing minutes, reconnect counts
