import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.scanner import Watchlist, WatchlistItem
from app.schemas.alert import WatchlistCreate, WatchlistItemAdd, WatchlistResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


@router.get("", response_model=List[WatchlistResponse])
async def get_user_watchlists(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id))
    wls = res.scalars().all()
    results = []
    for wl in wls:
        items_res = await db.execute(select(WatchlistItem.symbol).where(WatchlistItem.watchlist_id == wl.id))
        symbols = items_res.scalars().all()
        results.append(WatchlistResponse(
            id=wl.id,
            name=wl.name,
            description=wl.description,
            items=list(symbols),
            created_at=wl.created_at
        ))
    return results


@router.post("", response_model=WatchlistResponse)
async def create_watchlist(req: WatchlistCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wl = Watchlist(user_id=user.id, name=req.name, description=req.description)
    db.add(wl)
    await db.commit()
    await db.refresh(wl)
    return WatchlistResponse(
        id=wl.id,
        name=wl.name,
        description=wl.description,
        items=[],
        created_at=wl.created_at
    )


@router.post("/{watchlist_id}/items")
async def add_item_to_watchlist(
    watchlist_id: uuid.UUID,
    req: WatchlistItemAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wl = await db.get(Watchlist, watchlist_id)
    if not wl or wl.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")

    item = WatchlistItem(watchlist_id=wl.id, symbol=req.symbol.upper(), notes=req.notes)
    db.add(item)
    await db.commit()
    return {"success": True, "symbol": req.symbol.upper()}


@router.delete("/{watchlist_id}/items/{symbol}")
async def remove_item_from_watchlist(
    watchlist_id: uuid.UUID,
    symbol: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wl = await db.get(Watchlist, watchlist_id)
    if not wl or wl.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")

    res = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == wl.id,
            WatchlistItem.symbol == symbol.upper()
        )
    )
    item = res.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()
    return {"success": True, "removed": symbol.upper()}
