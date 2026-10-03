import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, delete
from app.core.config import settings
from app.core.errors import AppError, InsufficientFundsError, ResourceNotFoundError
from app.core.redis import redis_service
from app.models.order import Order, OrderEvent
from app.models.portfolio import Portfolio, PortfolioPosition, PortfolioTransaction
from app.models.wallet import Wallet, LedgerEntry
from app.models.instrument import Instrument
from app.providers.market_data.factory import get_market_data_provider
from app.services.wallet_service import WalletService
from app.services.charge_service import ChargeService
from app.services.portfolio_service import PortfolioService

logger = logging.getLogger("paper_trading_service")


class PaperTradingService:
    """Central deterministic Paper Trading Engine for Indian Equities."""

    @classmethod
    async def create_paper_order(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        symbol: str,
        side: str,
        order_type: str,
        quantity: int,
        price: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None,
        target_price: Optional[Decimal] = None,
        idempotency_key: Optional[str] = None,
        user_confirmed: bool = True
    ) -> Order:
        sym = symbol.upper()
        side_norm = side.upper()
        type_norm = order_type.upper()

        if side_norm not in ["BUY", "SELL"]:
            raise AppError(code="INVALID_SIDE", message="Order side must be BUY or SELL")
        if type_norm not in ["MARKET", "LIMIT", "SL", "SL_LIMIT"]:
            raise AppError(code="INVALID_ORDER_TYPE", message="Order type must be MARKET, LIMIT, SL, or SL_LIMIT")
        if quantity <= 0:
            raise AppError(code="INVALID_QUANTITY", message="Quantity must be greater than 0")

        # 1. Idempotency Check
        if idempotency_key:
            stmt = select(Order).where(
                and_(Order.user_id == user_id, Order.idempotency_key == idempotency_key)
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                logger.info(f"Idempotent order replay: returning existing order {existing.id}")
                return existing

        # Ensure user wallet & portfolio exist
        wallet = await WalletService.get_or_create_wallet(db, user_id)
        portfolio = await PortfolioService.get_or_create_portfolio(db, user_id)

        # 2. Get authoritative market quote from backend
        market_provider = get_market_data_provider()
        quote = await market_provider.get_quote(sym)
        market_price = Decimal(str(quote["price"]))
        quote_ts = quote.get("timestamp") or datetime.now(timezone.utc)

        # Determine reference price
        if type_norm == "MARKET":
            ref_price = market_price
        else:
            if price is None or price <= Decimal("0.00"):
                raise AppError(code="INVALID_LIMIT_PRICE", message="Limit price required for LIMIT orders")
            ref_price = price

        # 3. Create Order record in CREATED state
        order = Order(
            user_id=user_id,
            portfolio_id=portfolio.id,
            symbol=sym,
            side=side_norm,
            order_type=type_norm,
            quantity=quantity,
            price=ref_price,
            stop_loss=stop_loss,
            target=target_price,
            status="SUBMITTED",
            idempotency_key=idempotency_key,
            source_timestamp=quote_ts,
            risk_approved=True,
            user_confirmed=user_confirmed,
            charges=Decimal("0.00")
        )
        db.add(order)
        await db.flush()

        # Log CREATED event
        db.add(OrderEvent(
            order_id=order.id,
            event_type="CREATED",
            details={"requested_price": float(ref_price), "quantity": quantity, "mode": "PAPER"}
        ))

        # 4. Check if immediate execution is possible
        should_fill = False
        execution_price = None

        if type_norm == "MARKET":
            should_fill = True
            execution_price = ChargeService.apply_slippage(market_price, side_norm, "MARKET")
        elif type_norm == "LIMIT":
            if side_norm == "BUY" and market_price <= ref_price:
                should_fill = True
                execution_price = ref_price
            elif side_norm == "SELL" and market_price >= ref_price:
                should_fill = True
                execution_price = ref_price

        if should_fill and execution_price:
            await cls._execute_fill(db, order, wallet, portfolio, execution_price)
        else:
            # Order stays PENDING
            order.status = "PENDING"
            if side_norm == "BUY":
                # Lock cash for pending BUY limit order
                charges_dict = ChargeService.calculate_charges(sym, side_norm, ref_price, quantity, type_norm)
                lock_amount = (ref_price * Decimal(str(quantity))) + charges_dict["total_charges"]
                if Decimal(str(wallet.available_balance)) < lock_amount:
                    order.status = "REJECTED"
                    order.error_message = f"Insufficient funds to lock for pending order (₹{lock_amount:,.2f})"
                    db.add(OrderEvent(order_id=order.id, event_type="REJECTED", details={"reason": order.error_message}))
                    await db.commit()
                    return order

                wallet.available_balance = Decimal(str(wallet.available_balance)) - lock_amount
                wallet.locked_balance = Decimal(str(wallet.locked_balance)) + lock_amount
                db.add(LedgerEntry(
                    wallet_id=wallet.id,
                    reference=f"LOCK-{order.id.hex[:8].upper()}",
                    entry_type="ORDER_LOCK",
                    direction="DEBIT",
                    amount=lock_amount,
                    balance_after=wallet.available_balance,
                    status="POSTED",
                    description=f"Margin locked for pending BUY {quantity} {sym} @ ₹{ref_price:,.2f}"
                ))

            db.add(OrderEvent(
                order_id=order.id,
                event_type="PENDING",
                details={"limit_price": float(ref_price), "current_market_price": float(market_price)}
            ))

        await db.commit()
        await db.refresh(order)

        # Publish realtime order event over Redis / WebSocket
        await redis_service.publish("order:events", {
            "type": "ORDER_CREATED",
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side,
            "status": order.status,
            "price": float(order.price),
            "quantity": order.quantity
        })

        return order

    @classmethod
    async def _execute_fill(
        cls,
        db: AsyncSession,
        order: Order,
        wallet: Wallet,
        portfolio: Portfolio,
        execution_price: Decimal
    ) -> None:
        """Atomically fills an order, updates wallet, portfolio positions, and transactions."""
        qty = order.quantity
        sym = order.symbol
        charges_dict = ChargeService.calculate_charges(sym, order.side, execution_price, qty, order.order_type)
        total_charges = charges_dict["total_charges"]
        order_turnover = execution_price * Decimal(str(qty))
        now = datetime.now(timezone.utc)

        # Lookup instrument id for sector reference
        inst_res = await db.execute(select(Instrument).where(Instrument.symbol == sym))
        instrument = inst_res.scalar_one_or_none()
        sector = instrument.sector if instrument else "Equity"
        inst_id = instrument.id if instrument else None

        if order.side == "BUY":
            # Total funds required = Turnover + Charges
            total_buy_cost = order_turnover + total_charges
            
            # If order was previously PENDING, funds were locked in wallet.locked_balance
            if order.status == "PENDING":
                pending_locked = (order.price * Decimal(str(qty))) + total_charges
                wallet.locked_balance = max(Decimal("0.00"), Decimal(str(wallet.locked_balance)) - pending_locked)
                # Any diff between locked and actual total buy cost
                diff = total_buy_cost - pending_locked
                if diff > Decimal("0.00"):
                    if Decimal(str(wallet.available_balance)) < diff:
                        raise InsufficientFundsError(f"Insufficient funds for execution price ₹{execution_price:,.2f}")
                    wallet.available_balance = Decimal(str(wallet.available_balance)) - diff
                else:
                    wallet.available_balance = Decimal(str(wallet.available_balance)) + abs(diff)
            else:
                # Direct market fill from available balance
                if Decimal(str(wallet.available_balance)) < total_buy_cost:
                    raise InsufficientFundsError(f"Available balance ₹{wallet.available_balance:,.2f} insufficient for order cost ₹{total_buy_cost:,.2f}")
                wallet.available_balance = Decimal(str(wallet.available_balance)) - total_buy_cost

            # Record Ledger Entry
            db.add(LedgerEntry(
                wallet_id=wallet.id,
                reference=f"FILL-{order.id.hex[:8].upper()}",
                entry_type="TRADE_BUY",
                direction="DEBIT",
                amount=total_buy_cost,
                balance_after=wallet.available_balance,
                status="POSTED",
                description=f"Executed BUY {qty} {sym} @ ₹{execution_price:,.2f} (+₹{total_charges:,.2f} charges)",
                metadata_json={"charges": {k: float(v) for k, v in charges_dict.items()}}
            ))

            # Update or create Position (Decimal weighted average)
            pos_res = await db.execute(
                select(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio.id)
                .where(PortfolioPosition.symbol == sym)
            )
            position = pos_res.scalar_one_or_none()

            if position:
                old_qty = Decimal(str(position.quantity))
                old_avg = Decimal(str(position.average_price))
                new_qty_dec = Decimal(str(qty))
                total_qty = old_qty + new_qty_dec
                if total_qty > Decimal("0.00"):
                    new_avg = ((old_qty * old_avg) + (new_qty_dec * execution_price)) / total_qty
                    position.average_price = new_avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                position.quantity = int(total_qty)
                position.current_price = execution_price
                position.is_active = True
                if order.stop_loss:
                    position.stop_loss = order.stop_loss
                if order.target:
                    position.target_price = order.target
            else:
                position = PortfolioPosition(
                    portfolio_id=portfolio.id,
                    instrument_id=inst_id,
                    symbol=sym,
                    sector=sector,
                    quantity=qty,
                    average_price=execution_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    current_price=execution_price,
                    unrealized_pnl=Decimal("0.00"),
                    realized_pnl=Decimal("0.00"),
                    stop_loss=order.stop_loss,
                    target_price=order.target,
                    is_active=True
                )
                db.add(position)

            # Record BUY Transaction
            db.add(PortfolioTransaction(
                portfolio_id=portfolio.id,
                instrument_id=inst_id,
                symbol=sym,
                side="BUY",
                quantity=qty,
                price=execution_price,
                charges=total_charges,
                executed_at=now
            ))

        elif order.side == "SELL":
            # Find open position with concurrency check
            pos_res = await db.execute(
                select(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio.id)
                .where(PortfolioPosition.symbol == sym)
                .with_for_update()
            )
            position = pos_res.scalar_one_or_none()

            if not position or position.quantity < qty:
                owned = position.quantity if position else 0
                order.status = "REJECTED"
                order.error_message = f"Cannot sell {qty} shares; only own {owned} shares"
                db.add(OrderEvent(order_id=order.id, event_type="REJECTED", details={"reason": order.error_message}))
                return

            avg_price = Decimal(str(position.average_price))
            # Realized P&L = (execution_price - average_price) * quantity - charges
            realized_pnl = ((execution_price - avg_price) * Decimal(str(qty))) - total_charges
            realized_pnl = realized_pnl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Net sale proceeds credited to wallet = Turnover - Charges
            net_proceeds = order_turnover - total_charges
            wallet.available_balance = Decimal(str(wallet.available_balance)) + net_proceeds

            # Ledger Entry
            db.add(LedgerEntry(
                wallet_id=wallet.id,
                reference=f"FILL-{order.id.hex[:8].upper()}",
                entry_type="TRADE_SELL",
                direction="CREDIT",
                amount=net_proceeds,
                balance_after=wallet.available_balance,
                status="POSTED",
                description=f"Executed SELL {qty} {sym} @ ₹{execution_price:,.2f} (Net: ₹{net_proceeds:,.2f}, P&L: ₹{realized_pnl:,.2f})",
                metadata_json={"charges": {k: float(v) for k, v in charges_dict.items()}, "realized_pnl": float(realized_pnl)}
            ))

            # Update position
            position.quantity -= qty
            position.realized_pnl = (position.realized_pnl or Decimal("0.00")) + realized_pnl
            position.current_price = execution_price
            if position.quantity <= 0:
                position.quantity = 0
                position.is_active = False

            # Record SELL Transaction
            db.add(PortfolioTransaction(
                portfolio_id=portfolio.id,
                instrument_id=inst_id,
                symbol=sym,
                side="SELL",
                quantity=qty,
                price=execution_price,
                charges=total_charges,
                realized_pnl=realized_pnl,
                executed_at=now
            ))
            order.realized_pnl = realized_pnl

        # Mark Order as FILLED
        order.status = "FILLED"
        order.execution_price = execution_price
        order.charges = total_charges
        order.executed_at = now
        order.broker_order_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        # Write FILLED Event
        db.add(OrderEvent(
            order_id=order.id,
            event_type="FILLED",
            details={
                "execution_price": float(execution_price),
                "quantity": qty,
                "mode": "PAPER",
                "charges": float(total_charges),
                "realized_pnl": float(order.realized_pnl or 0)
            }
        ))

    @classmethod
    async def cancel_paper_order(cls, db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        order = await db.get(Order, order_id)
        if not order or order.user_id != user_id:
            raise ResourceNotFoundError("Order", order_id)

        if order.status != "PENDING":
            raise AppError(code="INVALID_STATE", message=f"Cannot cancel order in state {order.status}")

        wallet = await WalletService.get_or_create_wallet(db, user_id)

        # Release locked cash if BUY order
        if order.side == "BUY":
            charges_dict = ChargeService.calculate_charges(order.symbol, order.side, order.price, order.quantity, order.order_type)
            lock_amount = (order.price * Decimal(str(order.quantity))) + charges_dict["total_charges"]
            wallet.locked_balance = max(Decimal("0.00"), Decimal(str(wallet.locked_balance)) - lock_amount)
            wallet.available_balance = Decimal(str(wallet.available_balance)) + lock_amount

            db.add(LedgerEntry(
                wallet_id=wallet.id,
                reference=f"UNLOCK-{order.id.hex[:8].upper()}",
                entry_type="ORDER_UNLOCK",
                direction="CREDIT",
                amount=lock_amount,
                balance_after=wallet.available_balance,
                status="POSTED",
                description=f"Unlocked margin for cancelled order {order.id}"
            ))

        order.status = "CANCELLED"
        db.add(OrderEvent(order_id=order.id, event_type="CANCELLED", details={"cancelled_at": datetime.now(timezone.utc).isoformat()}))
        await db.commit()
        await db.refresh(order)

        await redis_service.publish("order:events", {
            "type": "ORDER_CANCELLED",
            "order_id": str(order.id),
            "symbol": order.symbol
        })
        return order

    @classmethod
    async def modify_paper_order(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
        new_quantity: Optional[int] = None,
        new_price: Optional[Decimal] = None,
        new_stop_loss: Optional[Decimal] = None,
        new_target: Optional[Decimal] = None
    ) -> Order:
        order = await db.get(Order, order_id)
        if not order or order.user_id != user_id:
            raise ResourceNotFoundError("Order", order_id)

        if order.status != "PENDING":
            raise AppError(code="INVALID_STATE", message=f"Only PENDING orders can be modified (current: {order.status})")

        wallet = await WalletService.get_or_create_wallet(db, user_id)

        # If price or quantity modified on BUY, adjust locked funds
        qty = new_quantity or order.quantity
        price = new_price or order.price

        if order.side == "BUY" and (new_quantity is not None or new_price is not None):
            old_charges = ChargeService.calculate_charges(order.symbol, order.side, order.price, order.quantity, order.order_type)["total_charges"]
            old_locked = (order.price * Decimal(str(order.quantity))) + old_charges

            new_charges = ChargeService.calculate_charges(order.symbol, order.side, price, qty, order.order_type)["total_charges"]
            new_required = (price * Decimal(str(qty))) + new_charges

            diff = new_required - old_locked
            if diff > Decimal("0.00"):
                if Decimal(str(wallet.available_balance)) < diff:
                    raise InsufficientFundsError(f"Insufficient funds to modify order (additional ₹{diff:,.2f} required)")
                wallet.available_balance = Decimal(str(wallet.available_balance)) - diff
                wallet.locked_balance = Decimal(str(wallet.locked_balance)) + diff
            elif diff < Decimal("0.00"):
                wallet.locked_balance = max(Decimal("0.00"), Decimal(str(wallet.locked_balance)) - abs(diff))
                wallet.available_balance = Decimal(str(wallet.available_balance)) + abs(diff)

        if new_quantity:
            order.quantity = new_quantity
        if new_price:
            order.price = new_price
        if new_stop_loss is not None:
            order.stop_loss = new_stop_loss
        if new_target is not None:
            order.target = new_target

        db.add(OrderEvent(
            order_id=order.id,
            event_type="MODIFIED",
            details={"price": float(order.price), "quantity": order.quantity, "sl": float(order.stop_loss) if order.stop_loss else None}
        ))
        await db.commit()
        await db.refresh(order)
        return order

    @classmethod
    async def evaluate_tick_triggers(cls, db: AsyncSession, symbol: str, current_price: Decimal) -> List[Dict[str, Any]]:
        """Evaluates pending LIMIT orders and position Stop Loss / Target triggers against incoming tick."""
        sym = symbol.upper()
        executed_events = []

        # 1. Evaluate PENDING LIMIT Orders
        stmt = select(Order).where(
            and_(Order.symbol == sym, Order.status == "PENDING")
        )
        res = await db.execute(stmt)
        pending_orders = res.scalars().all()

        for ord in pending_orders:
            should_fill = False
            if ord.order_type in ["LIMIT", "MARKET"]:
                if ord.side == "BUY" and current_price <= ord.price:
                    should_fill = True
                elif ord.side == "SELL" and current_price >= ord.price:
                    should_fill = True

            if should_fill:
                wallet = await db.get(Wallet, ord.user_id) or await WalletService.get_or_create_wallet(db, ord.user_id)
                portfolio = await db.get(Portfolio, ord.portfolio_id) or await PortfolioService.get_or_create_portfolio(db, ord.user_id)
                try:
                    await cls._execute_fill(db, ord, wallet, portfolio, ord.price)
                    executed_events.append({"type": "LIMIT_FILLED", "order_id": str(ord.id), "symbol": sym, "price": float(ord.price)})
                except Exception as e:
                    logger.error(f"Error executing limit fill for order {ord.id}: {e}")

        # 2. Evaluate Stop-Loss & Target Triggers on Open Positions
        pos_stmt = select(PortfolioPosition).where(
            and_(
                PortfolioPosition.symbol == sym,
                PortfolioPosition.quantity > 0,
                PortfolioPosition.is_active == True
            )
        )
        pos_res = await db.execute(pos_stmt)
        active_positions = pos_res.scalars().all()

        for pos in active_positions:
            portfolio = await db.get(Portfolio, pos.portfolio_id)
            if not portfolio:
                continue
            user_id = portfolio.user_id
            wallet = await WalletService.get_or_create_wallet(db, user_id)

            # Stop Loss trigger check (for long position: current_price <= stop_loss)
            if pos.stop_loss and current_price <= pos.stop_loss:
                logger.info(f"Stop-loss triggered for {sym} at ₹{current_price} <= ₹{pos.stop_loss}")
                sl_order = Order(
                    user_id=user_id,
                    portfolio_id=portfolio.id,
                    symbol=sym,
                    side="SELL",
                    order_type="MARKET",
                    quantity=pos.quantity,
                    price=current_price,
                    status="SUBMITTED",
                    risk_approved=True,
                    user_confirmed=True
                )
                db.add(sl_order)
                await db.flush()

                db.add(OrderEvent(
                    order_id=sl_order.id,
                    event_type="STOPLOSS_TRIGGERED",
                    details={"trigger_price": float(current_price), "stop_loss": float(pos.stop_loss)}
                ))
                await cls._execute_fill(db, sl_order, wallet, portfolio, current_price)
                executed_events.append({"type": "STOPLOSS_TRIGGERED", "symbol": sym, "price": float(current_price)})

            # Target Price trigger check (for long position: current_price >= target_price)
            elif pos.target_price and current_price >= pos.target_price:
                logger.info(f"Target triggered for {sym} at ₹{current_price} >= ₹{pos.target_price}")
                target_order = Order(
                    user_id=user_id,
                    portfolio_id=portfolio.id,
                    symbol=sym,
                    side="SELL",
                    order_type="MARKET",
                    quantity=pos.quantity,
                    price=current_price,
                    status="SUBMITTED",
                    risk_approved=True,
                    user_confirmed=True
                )
                db.add(target_order)
                await db.flush()

                db.add(OrderEvent(
                    order_id=target_order.id,
                    event_type="TARGET_TRIGGERED",
                    details={"trigger_price": float(current_price), "target_price": float(pos.target_price)}
                ))
                await cls._execute_fill(db, target_order, wallet, portfolio, current_price)
                executed_events.append({"type": "TARGET_TRIGGERED", "symbol": sym, "price": float(current_price)})

        if executed_events:
            await db.commit()
            for evt in executed_events:
                await redis_service.publish("order:events", evt)

        return executed_events

    @classmethod
    async def reset_paper_account(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        clear_history: bool = True
    ) -> Dict[str, Any]:
        """Authenticated development/demo endpoint: cancels pending paper orders, closes positions, resets paper wallet."""
        if settings.TRADING_MODE != "PAPER" and settings.APP_ENV not in ["development", "test"]:
            raise AppError(code="FORBIDDEN_LIVE_MODE", message="Paper trading reset is strictly prohibited in live mode")

        wallet = await WalletService.get_or_create_wallet(db, user_id)
        portfolio = await PortfolioService.get_or_create_portfolio(db, user_id)

        # 1. Cancel all pending orders
        ord_res = await db.execute(
            select(Order).where(and_(Order.user_id == user_id, Order.status == "PENDING"))
        )
        for pending_ord in ord_res.scalars().all():
            pending_ord.status = "CANCELLED"
            db.add(OrderEvent(order_id=pending_ord.id, event_type="CANCELLED", details={"reason": "DEMO_ACCOUNT_RESET"}))

        # 2. Reset wallet balance to ₹10,00,000
        starting_capital = Decimal("1000000.00")
        wallet.available_balance = starting_capital
        wallet.locked_balance = Decimal("0.00")

        # 3. Clear/deactivate all positions
        pos_res = await db.execute(select(PortfolioPosition).where(PortfolioPosition.portfolio_id == portfolio.id))
        for pos in pos_res.scalars().all():
            pos.quantity = 0
            pos.average_price = Decimal("0.00")
            pos.unrealized_pnl = Decimal("0.00")
            pos.realized_pnl = Decimal("0.00")
            pos.is_active = False

        # 4. Clear transactions and ledger if explicitly requested
        if clear_history:
            # Delete transactions
            await db.execute(delete(PortfolioTransaction).where(PortfolioTransaction.portfolio_id == portfolio.id))
            # Reset ledger with initial paper capital
            await db.execute(delete(LedgerEntry).where(LedgerEntry.wallet_id == wallet.id))
            db.add(LedgerEntry(
                wallet_id=wallet.id,
                reference=f"RESET-PAPER-{uuid.uuid4().hex[:8].upper()}",
                entry_type="DEPOSIT",
                direction="CREDIT",
                amount=starting_capital,
                balance_after=starting_capital,
                status="POSTED",
                description="Demo paper account reset to initial capital ₹10,00,000",
                metadata_json={"type": "DEMO_ACCOUNT_RESET"}
            ))

        await db.commit()
        await db.refresh(wallet)

        return {
            "mode": "PAPER",
            "status": "RESET_SUCCESSFUL",
            "available_cash": float(wallet.available_balance),
            "locked_cash": float(wallet.locked_balance),
            "positions_count": 0,
            "message": "Paper trading account successfully reset to ₹10,00,000 with zero active holdings."
        }
