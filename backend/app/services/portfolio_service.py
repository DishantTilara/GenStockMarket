import uuid
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Portfolio, PortfolioPosition
from app.providers.market_data.factory import get_market_data_provider
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
            await db.flush()

            # Seed realistic initial bluechip holdings
            initial_positions = [
                {"symbol": "RELIANCE", "quantity": 100, "average_price": Decimal("2850.00"), "sector": "Energy"},
                {"symbol": "TCS", "quantity": 75, "average_price": Decimal("4100.00"), "sector": "IT"},
                {"symbol": "HDFCBANK", "quantity": 200, "average_price": Decimal("1620.00"), "sector": "Banking"},
                {"symbol": "INFY", "quantity": 150, "average_price": Decimal("1840.00"), "sector": "IT"},
            ]
            for p in initial_positions:
                pos = PortfolioPosition(
                    portfolio_id=portfolio.id,
                    symbol=p["symbol"],
                    quantity=p["quantity"],
                    average_price=p["average_price"],
                    current_price=p["average_price"],
                    unrealized_pnl=Decimal("0.00"),
                    realized_pnl=Decimal("0.00"),
                    sector=p["sector"]
                )
                db.add(pos)

            await db.commit()
            await db.refresh(portfolio)

        return portfolio

    @classmethod
    async def get_portfolio_summary(cls, db: AsyncSession, user_id: uuid.UUID) -> PortfolioResponse:
        portfolio = await cls.get_or_create_portfolio(db, user_id)
        market_provider = get_market_data_provider()

        pos_res = await db.execute(select(PortfolioPosition).where(PortfolioPosition.portfolio_id == portfolio.id))
        db_positions = pos_res.scalars().all()

        total_invested = Decimal("0.00")
        current_value = Decimal("0.00")
        sector_totals: Dict[str, Decimal] = {}
        position_responses: List[PortfolioPositionResponse] = []

        for p in db_positions:
            quote = await market_provider.get_quote(p.symbol)
            cur_price = Decimal(str(quote["price"]))
            p.current_price = cur_price
            
            invested = p.average_price * p.quantity
            val = cur_price * p.quantity
            pnl = val - invested
            pnl_pct = ((cur_price - p.average_price) / p.average_price * 100) if p.average_price else Decimal("0.00")
            
            p.unrealized_pnl = pnl

            total_invested += invested
            current_value += val

            sector = p.sector or "Other"
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
                unrealized_pnl_pct=round(pnl_pct, 2)
            ))

        await db.commit()

        total_unrealized_pnl = current_value - total_invested
        total_pnl_pct = (total_unrealized_pnl / total_invested * 100) if total_invested else Decimal("0.00")

        # Sector percentage allocation
        sector_allocation = {}
        if current_value > Decimal("0.00"):
            for sec, amt in sector_totals.items():
                sector_allocation[sec] = round((amt / current_value) * 100, 2)

        return PortfolioResponse(
            id=portfolio.id,
            name=portfolio.name,
            total_invested=round(total_invested, 2),
            current_value=round(current_value, 2),
            total_unrealized_pnl=round(total_unrealized_pnl, 2),
            total_unrealized_pnl_pct=round(total_pnl_pct, 2),
            cash_balance=Decimal("250000.00"),
            positions=position_responses,
            sector_allocation=sector_allocation
        )

    @classmethod
    async def analyze_portfolio(cls, db: AsyncSession, user_id: uuid.UUID) -> PortfolioAnalysisResponse:
        summary = await cls.get_portfolio_summary(db, user_id)
        
        # Sort positions by unrealized pnl
        sorted_by_pnl = sorted(summary.positions, key=lambda x: x.unrealized_pnl, reverse=True)
        contributors = [{"symbol": p.symbol, "pnl": float(p.unrealized_pnl), "pnl_pct": float(p.unrealized_pnl_pct)} for p in sorted_by_pnl if p.unrealized_pnl >= 0]
        detractors = [{"symbol": p.symbol, "pnl": float(p.unrealized_pnl), "pnl_pct": float(p.unrealized_pnl_pct)} for p in sorted_by_pnl if p.unrealized_pnl < 0]

        concentration_risks = []
        for p in summary.positions:
            pos_weight = (p.current_value / summary.current_value * 100) if summary.current_value else 0
            if pos_weight > 25:
                concentration_risks.append(f"{p.symbol} represents {pos_weight:.1f}% of total portfolio value (Above recommended 25% single-stock ceiling)")

        sector_floats = {k: float(v) for k, v in summary.sector_allocation.items()}
        diversification = []
        if sector_floats.get("IT", 0) > 40:
            diversification.append("High IT sector exposure detected. Consider rebalancing into defensive sectors (FMCG/Pharma).")
        if len(summary.positions) < 5:
            diversification.append("Portfolio contains fewer than 5 active positions. Broaden exposure across uncorrelated sectors.")

        return PortfolioAnalysisResponse(
            summary=f"Portfolio value is ₹{summary.current_value:,.2f} with total unrealized P&L of ₹{summary.total_unrealized_pnl:,.2f} ({summary.total_unrealized_pnl_pct:+.2f}%).",
            largest_contributors=contributors[:3],
            largest_detractors=detractors[:3],
            concentration_risks=concentration_risks,
            sector_exposure=sector_floats,
            diversification_observations=diversification
        )
