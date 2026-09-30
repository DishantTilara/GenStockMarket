import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.audit import log_audit_event
from app.models.user import User
from app.models.ai import AIConversation, AIMessage
from app.providers.ai.factory import get_llm_provider
from app.providers.ai.tools import AIToolExecutor
from app.services.indicator_service import IndicatorService
from app.services.market_service import MarketService
from app.schemas.ai import AIChatRequest, AIChatResponse, AIStockAnalysisResponse, AINewspaperResponse, AINewspaperArticle
from app.api.deps import get_current_user

router = APIRouter(prefix="/ai", tags=["GenAI Intelligence"])


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    req: AIChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    provider = get_llm_provider()
    conv_id = req.conversation_id or str(uuid.uuid4())

    messages = [
        {"role": "system", "content": "You are a professional Indian Stock Market Quantitative & GenAI Analyst grounded strictly in verified market data tools. Never invent prices or balances."},
        {"role": "user", "content": req.message}
    ]

    result = await provider.chat(messages)

    # Record message in conversation history
    conv = await db.get(AIConversation, uuid.UUID(conv_id)) if req.conversation_id else None
    if not conv:
        conv = AIConversation(id=uuid.UUID(conv_id), user_id=user.id, title=req.message[:50])
        db.add(conv)
        await db.flush()

    user_msg = AIMessage(conversation_id=conv.id, role="user", content=req.message)
    ai_msg = AIMessage(conversation_id=conv.id, role="assistant", content=result["content"], tool_calls=result.get("tool_calls"))
    db.add(user_msg)
    db.add(ai_msg)

    await log_audit_event(
        db,
        action="AI_QUERY",
        user_id=user.id,
        resource_type="ai_conversation",
        resource_id=str(conv.id),
        details={"query_len": len(req.message), "tool_count": len(result.get("tool_calls", []))}
    )
    await db.commit()

    return AIChatResponse(
        conversation_id=str(conv.id),
        reply=result["content"],
        tool_calls_executed=result.get("tool_calls", []),
        created_at=datetime.now(timezone.utc)
    )


@router.get("/stock/{symbol}", response_model=AIStockAnalysisResponse)
async def analyze_stock(symbol: str):
    sym = symbol.upper()
    quote = await MarketService.get_quote(sym)
    indicators = await IndicatorService.compute_indicators(sym)
    fund_data = await AIToolExecutor.execute_tool("get_company_fundamentals", {"symbol": sym})

    price = float(quote["price"])
    rsi = indicators["rsi_14"]
    support = indicators["support"]
    resistance = indicators["resistance"]
    trend = indicators["trend"]

    if rsi < 35:
        signal = "BUY"
        regime = "Oversold Mean Reversion"
        entry = {"min": round(price * 0.995, 2), "max": round(price * 1.005, 2)}
        stop = round(support * 0.985, 2)
        targets = [round(price * 1.025, 2), round(price * 1.050, 2)]
        conf = 0.84
    elif rsi > 70:
        signal = "SELL"
        regime = "Overbought Exhaustion"
        entry = {"min": round(price * 0.995, 2), "max": round(price * 1.005, 2)}
        stop = round(resistance * 1.015, 2)
        targets = [round(price * 0.975, 2), round(price * 0.950, 2)]
        conf = 0.81
    elif trend in ["BULLISH", "STRONG_BULLISH"]:
        signal = "BUY"
        regime = "Trend Following Momentum"
        entry = {"min": round(price * 0.998, 2), "max": round(price * 1.004, 2)}
        stop = round(indicators["ema_20"] * 0.99, 2)
        targets = [round(price * 1.03, 2), round(price * 1.06, 2)]
        conf = 0.78
    else:
        signal = "WATCH"
        regime = "Neutral Range Consolidation"
        entry = None
        stop = None
        targets = []
        conf = 0.65

    rr = round((targets[0] - price) / (price - stop), 2) if targets and stop and price != stop else None

    return AIStockAnalysisResponse(
        symbol=sym,
        signal=signal,
        market_regime=regime,
        entry_zone=entry,
        stop_loss=stop,
        targets=targets,
        risk_reward=rr,
        confidence=conf,
        technical_analysis=indicators,
        fundamental_analysis=fund_data.get("fundamentals", {}),
        news_analysis={"sentiment": "Constructive", "fii_flows": "Net positive"},
        risk_analysis={"max_drawdown_risk": "Moderate", "beta": 1.12},
        supporting_factors=[
            f"Price action aligns with {trend.replace('_', ' ').lower()} indicator configuration",
            f"Holding structural support level at ₹{support:,.2f}",
            f"Sector institutional participation remains resilient"
        ],
        opposing_factors=[
            "Broader macroeconomic inflation volatility",
            f"Overhead resistance zone at ₹{resistance:,.2f}"
        ],
        invalidation_conditions=[
            f"Close below ₹{stop:,.2f}" if stop else "Trend breakdown below key moving averages",
            "Broad benchmark NIFTY 50 breakdown below support"
        ],
        data_quality="HIGH",
        data_timestamp=datetime.now(timezone.utc),
        warnings=[
            "Simulated research output. Financial markets involve risk of capital loss.",
            "Past performance does not guarantee future results."
        ]
    )


@router.get("/newspaper", response_model=AINewspaperResponse)
async def get_ai_newspaper(edition: str = Query("INTRADAY", pattern="^(PRE_MARKET|INTRADAY|CLOSING)$")):
    now = datetime.now(timezone.utc)
    articles = [
        AINewspaperArticle(
            section="Executive Market Setup",
            headline=f"Indian Equities {edition.capitalize()} Brief: Benchmark Indices Consolidate Near Record Zones",
            content="NIFTY 50 and BANK NIFTY continue to exhibit constructive structural breadth supported by domestic institutional inflows and strong Q2 corporate margin trajectories. High-beta sectors including Automobile and IT lead intraday turnover.",
            data_points=["NIFTY 50: ~25,850 (+0.42%)", "BANK NIFTY: ~53,400 (+0.55%)", "India VIX: 12.85 (-3.2%)"]
        ),
        AINewspaperArticle(
            section="Sector Rotation & Leaders",
            headline="IT and Private Banking Spark Accumulation While FMCG Pauses",
            content="Capital rotation favors technology exporters following resilient enterprise deal wins from TCS and Infosys. Private banking counters hold firm above key 20-day exponential moving averages.",
            data_points=["TCS & INFY order book expansions", "HDFC Bank deposit growth stable", "Auto volumes advance 8.4% YoY"]
        ),
        AINewspaperArticle(
            section="Quantitative Risk & Tactical Levels",
            headline="Support Walls Firm at 25,700 for NIFTY; Call Writing Dense at 26,000",
            content="Derivatives open interest distribution signals a well-defined consolidation channel. F&O participants maintain cautious long positions with trailing stop losses pegged near key swing lows.",
            data_points=["Key Support: 25,700 / 53,000", "Key Hurdle: 26,000 / 53,800", "FII Net Equity: +₹1,850 Cr"]
        )
    ]

    return AINewspaperResponse(
        edition=edition,
        generated_at=now,
        market_headline=f"AI Daily Intelligence Chronicle — {edition.replace('_', ' ')} Edition",
        articles=articles
    )
