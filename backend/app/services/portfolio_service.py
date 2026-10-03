import uuid
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.portfolio import Portfolio, PortfolioPosition, PortfolioTransaction
from app.models.order import Order, OrderEvent
from app.models.wallet import Wallet, LedgerEntry
from app.providers.market_data.factory import get_market_data_provider
from app.services.wallet_service import WalletService
from app.schemas.portfolio import PortfolioResponse, PortfolioPositionResponse, PortfolioAnalysisResponse


class PortfolioService:
    @staticmethod
    async def get_or_create_portfolio(db: AsyncSession, user_id: uuid.UUID) -> Portfolio:
        res = await db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
        portfolio = res.scalar_one_or_none()
        if not portfolio:
            portfolio = Portfolio(
                user_id=user_id,
                name="Main Portfolio",
                initial_cash=Decimal("1000000.00")
            )
            db.add(portfolio)
            await db.commit()
            await db.refresh(portfolio)

        # Also ensure wallet exists for user
        await WalletService.get_or_create_wallet(db, user_id)
        return portfolio

    @classmethod
    async def get_portfolio_summary(cls, db: AsyncSession, user_id: uuid.UUID) -> PortfolioResponse:
        portfolio = await cls.get_or_create_portfolio(db, user_id)
        wallet = await WalletService.get_or_create_wallet(db, user_id)
        market_provider = get_market_data_provider()

        pos_res = await db.execute(
            select(PortfolioPosition)
            .where(PortfolioPosition.portfolio_id == portfolio.id)
            .where(PortfolioPosition.quantity > 0)
        )
        db_positions = pos_res.scalars().all()

        # Realized P&L from ALL positions (both active and closed)
        all_pos_res = await db.execute(
            select(PortfolioPosition).where(PortfolioPosition.portfolio_id == portfolio.id)
        )
        total_realized_pnl = sum([Decimal(str(p.realized_pnl or 0)) for p in all_pos_res.scalars().all()], Decimal("0.00"))

        total_invested = Decimal("0.00")
        current_value = Decimal("0.00")
        sector_totals: Dict[str, Decimal] = {}
        position_responses: List[PortfolioPositionResponse] = []

        for p in db_positions:
            quote = await market_provider.get_quote(p.symbol)
            cur_price = Decimal(str(quote["price"])) if quote and "price" in quote else p.average_price
            p.current_price = cur_price

            invested = p.average_price * Decimal(str(p.quantity))
            val = cur_price * Decimal(str(p.quantity))
            pnl = val - invested
            pnl_pct = ((cur_price - p.average_price) / p.average_price * Decimal("100")) if p.average_price else Decimal("0.00")

            p.unrealized_pnl = pnl

            total_invested += invested
            current_value += val

            sector = p.sector or "Equity"
            sector_totals[sector] = sector_totals.get(sector, Decimal("0.00")) + val

            position_responses.append(PortfolioPositionResponse(
                id=p.id,
                symbol=p.symbol,
                sector=p.sector,
                quantity=p.quantity,
                average_price=p.average_price,
                current_price=cur_price,
                invested_amount=round(invested, 2),
                current_value=round(val, 2),
                unrealized_pnl=round(pnl, 2),
                unrealized_pnl_pct=round(pnl_pct, 2),
                realized_pnl=round(Decimal(str(p.realized_pnl or 0)), 2),
                stop_loss=p.stop_loss,
                target_price=p.target_price
            ))

        await db.commit()

        total_unrealized_pnl = current_value - total_invested
        total_unrealized_pnl_pct = (total_unrealized_pnl / total_invested * Decimal("100")) if total_invested > Decimal("0.00") else Decimal("0.00")
        
        # Authoritative cash balance comes from paper wallet
        cash_balance = Decimal(str(wallet.available_balance))
        total_equity = cash_balance + current_value
        total_pnl = total_unrealized_pnl + total_realized_pnl

        # Calculate today's P&L (compared against starting capital or beginning of day)
        starting_capital = portfolio.initial_cash or Decimal("1000000.00")
        today_pnl = total_equity - starting_capital
        today_pnl_pct = (today_pnl / starting_capital * Decimal("100")) if starting_capital else Decimal("0.00")

        # Sector percentage allocation
        sector_allocation = {}
        if current_value > Decimal("0.00"):
            for sec, amt in sector_totals.items():
                sector_allocation[sec] = round((amt / current_value) * Decimal("100"), 2)

        return PortfolioResponse(
            id=portfolio.id,
            name=portfolio.name,
            total_invested=round(total_invested, 2),
            current_value=round(current_value, 2),
            total_unrealized_pnl=round(total_unrealized_pnl, 2),
            total_unrealized_pnl_pct=round(total_unrealized_pnl_pct, 2),
            realized_pnl=round(total_realized_pnl, 2),
            total_pnl=round(total_pnl, 2),
            today_pnl=round(today_pnl, 2),
            today_pnl_pct=round(today_pnl_pct, 2),
            cash_balance=round(cash_balance, 2),
            total_equity=round(total_equity, 2),
            positions=position_responses,
            sector_allocation=sector_allocation
        )

    @classmethod
    async def analyze_portfolio(cls, db: AsyncSession, user_id: uuid.UUID) -> PortfolioAnalysisResponse:
        summary = await cls.get_portfolio_summary(db, user_id)

        if not summary.positions:
            return PortfolioAnalysisResponse(
                summary="Portfolio currently has no active holdings. Use paper trading to place BUY orders.",
                largest_contributors=[],
                largest_detractors=[],
                concentration_risks=[],
                sector_exposure={},
                diversification_observations=["No positions currently open."]
            )

        # Sort positions by unrealized pnl
        sorted_by_pnl = sorted(summary.positions, key=lambda x: x.unrealized_pnl, reverse=True)
        contributors = [{"symbol": p.symbol, "pnl": float(p.unrealized_pnl), "pnl_pct": float(p.unrealized_pnl_pct)} for p in sorted_by_pnl if p.unrealized_pnl >= 0]
        detractors = [{"symbol": p.symbol, "pnl": float(p.unrealized_pnl), "pnl_pct": float(p.unrealized_pnl_pct)} for p in sorted_by_pnl if p.unrealized_pnl < 0]

        concentration_risks = []
        for p in summary.positions:
            pos_weight = (p.current_value / summary.current_value * Decimal("100")) if summary.current_value else Decimal("0.0")
            if pos_weight > Decimal("25.0"):
                concentration_risks.append(f"{p.symbol} represents {float(pos_weight):.1f}% of total position value (Above 25% single-stock ceiling)")

        sector_floats = {k: float(v) for k, v in summary.sector_allocation.items()}
        diversification = []
        if sector_floats.get("IT", 0) > 40:
            diversification.append("High IT sector exposure. Consider diversifying across defensive sectors.")
        if len(summary.positions) < 3:
            diversification.append("Portfolio has fewer than 3 positions. Broaden sector coverage.")

        return PortfolioAnalysisResponse(
            summary=f"Portfolio Equity: ₹{summary.total_equity:,.2f}, Position Value: ₹{summary.current_value:,.2f}, Unrealized P&L: ₹{summary.total_unrealized_pnl:,.2f} ({summary.total_unrealized_pnl_pct:+.2f}%).",
            largest_contributors=contributors[:3],
            largest_detractors=detractors[:3],
            concentration_risks=concentration_risks,
            sector_exposure=sector_floats,
            diversification_observations=diversification
        )
