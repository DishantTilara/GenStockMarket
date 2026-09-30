import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.alert import Alert, AlertEvent
from app.schemas.alert import AlertCreate, AlertResponse, AlertEventResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertResponse])
async def get_alerts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc()))
    return list(res.scalars().all())


@router.post("", response_model=AlertResponse)
async def create_alert(req: AlertCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    alert = Alert(
        user_id=user.id,
        symbol=req.symbol.upper(),
        condition_type=req.condition_type,
        target_value=req.target_value,
        is_active=True,
        is_triggered=False
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}")
async def delete_alert(alert_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert or alert.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
    return {"success": True, "deleted": alert_id}


@router.get("/history", response_model=List[AlertEventResponse])
async def get_alert_history(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AlertEvent).where(AlertEvent.user_id == user.id).order_by(AlertEvent.triggered_at.desc()).limit(50))
    return list(res.scalars().all())
