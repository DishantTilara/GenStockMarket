from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.services.portfolio_service import PortfolioService
from app.schemas.portfolio import PortfolioResponse, PortfolioAnalysisResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PortfolioService.get_portfolio_summary(db, user.id)


@router.get("/analysis", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PortfolioService.analyze_portfolio(db, user.id)
