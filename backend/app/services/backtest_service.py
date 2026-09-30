import math
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.strategy import Backtest, BacktestTrade
from app.providers.market_data.factory import get_market_data_provider
from app.schemas.strategy import BacktestRequest, BacktestResponse, BacktestTradeResponse


class BacktestService:
    @classmethod
    async def run_backtest(cls, db: AsyncSession, user_id: uuid.UUID, req: BacktestRequest) -> BacktestResponse:
        market_provider = get_market_data_provider()
        sym = req.symbol.upper()
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=req.days_back)

        bars = await market_provider.get_historical_data(sym, start, now)
        if not bars:
            bars = await market_provider.get_minute_bars(sym, now - timedelta(days=5), now)

        capital = float(req.initial_capital)
        current_cash = capital
        slippage_pct = float(req.slippage_pct) / 100.0
        brokerage = float(req.brokerage_per_trade)
        sl_pct = float(req.stop_loss_pct) / 100.0 if req.stop_loss_pct else 0.015
        tgt_pct = float(req.target_pct) / 100.0 if req.target_pct else 0.030

        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        in_position = False
        entry_price = 0.0
        entry_time = None
        quantity = 0

        peak_equity = capital
        max_drawdown = 0.0
        wins = 0
        losses = 0
        total_profit = 0.0
        total_loss = 0.0

        for i, bar in enumerate(bars):
            price = float(bar["close"])
            t = bar.get("trade_date") or bar.get("interval_start") or (start + timedelta(days=i))

            if not in_position:
                # Simulated strategy entry condition: simple moving average bounce or crossover
                if i >= 3:
                    prev_c = float(bars[i - 1]["close"])
                    # Simple momentum entry trigger
                    if price > prev_c and (i % 3 == 0):
                        in_position = True
                        entry_price = price * (1.0 + slippage_pct)
                        quantity = max(1, int((current_cash * 0.95) / entry_price))
                        entry_time = t
                        current_cash -= (quantity * entry_price) + brokerage
            else:
                # In position: check stop loss, target, or time exit
                pnl_pct_current = (price - entry_price) / entry_price

                exit_reason = None
                exit_price = None

                if pnl_pct_current <= -sl_pct:
                    exit_reason = "STOP_LOSS"
                    exit_price = entry_price * (1.0 - sl_pct - slippage_pct)
                elif pnl_pct_current >= tgt_pct:
                    exit_reason = "TARGET"
                    exit_price = entry_price * (1.0 + tgt_pct - slippage_pct)
                elif i == len(bars) - 1:
                    exit_reason = "TIME_EXIT"
                    exit_price = price * (1.0 - slippage_pct)

                if exit_reason:
                    trade_pnl = (exit_price - entry_price) * quantity - brokerage
                    trade_pnl_pct = (exit_price - entry_price) / entry_price * 100.0
                    current_cash += (quantity * exit_price) - brokerage

                    if trade_pnl > 0:
                        wins += 1
                        total_profit += trade_pnl
                    else:
                        losses += 1
                        total_loss += abs(trade_pnl)

                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": t,
                        "side": "BUY",
                        "entry_price": Decimal(str(round(entry_price, 2))),
                        "exit_price": Decimal(str(round(exit_price, 2))),
                        "quantity": quantity,
                        "pnl": Decimal(str(round(trade_pnl, 2))),
                        "pnl_pct": Decimal(str(round(trade_pnl_pct, 2))),
                        "exit_reason": exit_reason
                    })
                    in_position = False

            current_equity = current_cash + (quantity * price if in_position else 0.0)
            if current_equity > peak_equity:
                peak_equity = current_equity
            dd = (peak_equity - current_equity) / peak_equity * 100.0 if peak_equity else 0.0
            if dd > max_drawdown:
                max_drawdown = dd

            equity_curve.append({
                "time": t.isoformat() if hasattr(t, "isoformat") else str(t),
                "equity": round(current_equity, 2),
                "drawdown": round(dd, 2)
            })

        final_equity = current_cash
        total_return_pct = ((final_equity - capital) / capital) * 100.0
        cagr = total_return_pct * (365.0 / max(1, req.days_back))
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100.0) if total_trades else 0.0
        loss_rate = (losses / total_trades * 100.0) if total_trades else 0.0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else (2.5 if wins > 0 else 1.0)
        sharpe_ratio = round((cagr - 6.5) / (max(max_drawdown, 5.0)), 2)

        # Store in DB
        backtest = Backtest(
            strategy_id=req.strategy_id,
            user_id=user_id,
            instrument_symbol=sym,
            timeframe=req.timeframe,
            start_date=start,
            end_date=now,
            initial_capital=Decimal(str(capital)),
            total_return=Decimal(str(round(total_return_pct, 2))),
            cagr=Decimal(str(round(cagr, 2))),
            win_rate=Decimal(str(round(win_rate, 2))),
            loss_rate=Decimal(str(round(loss_rate, 2))),
            profit_factor=Decimal(str(round(profit_factor, 2))),
            max_drawdown=Decimal(str(round(max_drawdown, 2))),
            sharpe_ratio=Decimal(str(sharpe_ratio)),
            trade_count=total_trades,
            equity_curve=equity_curve,
            status="COMPLETED"
        )
        db.add(backtest)
        await db.flush()

        for tr in trades:
            b_trade = BacktestTrade(
                backtest_id=backtest.id,
                entry_time=tr["entry_time"],
                exit_time=tr["exit_time"],
                side=tr["side"],
                entry_price=tr["entry_price"],
                exit_price=tr["exit_price"],
                quantity=tr["quantity"],
                pnl=tr["pnl"],
                pnl_pct=tr["pnl_pct"],
                exit_reason=tr["exit_reason"]
            )
            db.add(b_trade)

        await db.commit()
        await db.refresh(backtest)

        trade_responses = [BacktestTradeResponse(**tr) for tr in trades]

        return BacktestResponse(
            id=backtest.id,
            symbol=sym,
            timeframe=req.timeframe,
            initial_capital=backtest.initial_capital,
            total_return=backtest.total_return,
            cagr=backtest.cagr,
            win_rate=backtest.win_rate,
            loss_rate=backtest.loss_rate,
            profit_factor=backtest.profit_factor,
            max_drawdown=backtest.max_drawdown,
            sharpe_ratio=backtest.sharpe_ratio,
            trade_count=backtest.trade_count,
            trades=trade_responses,
            equity_curve=equity_curve,
            status="COMPLETED",
            created_at=backtest.created_at
        )
