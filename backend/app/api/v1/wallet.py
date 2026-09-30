import uuid
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.audit import log_audit_event
from app.models.user import User
from app.models.wallet import DepositRequest, WithdrawalRequest
from app.schemas.wallet import WalletResponse, DepositRequestCreate, DepositResponse, WithdrawalRequestCreate, WithdrawalResponse, LedgerEntryResponse
from app.services.wallet_service import WalletService
from app.api.deps import get_current_user

router = APIRouter(prefix="/wallet", tags=["Wallet & Ledger"])


@router.get("", response_model=WalletResponse)
async def get_wallet(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wallet = await WalletService.get_or_create_wallet(db, user.id)
    avail = Decimal(str(wallet.available_balance))
    locked = Decimal(str(wallet.locked_balance))
    return WalletResponse(
        id=wallet.id,
        available_balance=avail,
        locked_balance=locked,
        total_balance=avail + locked,
        currency=wallet.currency
    )


@router.post("/deposit", response_model=DepositResponse)
async def deposit_funds(
    req: DepositRequestCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    deposit, ledger = await WalletService.process_deposit(db, user.id, req)
    await log_audit_event(
        db,
        action="WALLET_DEPOSIT",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        resource_type="deposit_request",
        resource_id=str(deposit.id),
        details={"amount": str(deposit.amount), "idempotency_key": req.idempotency_key}
    )
    return DepositResponse(
        deposit_id=deposit.id,
        wallet_id=deposit.wallet_id,
        amount=deposit.amount,
        status=deposit.status,
        reference_id=deposit.reference_id,
        message="Deposit completed successfully. Funds credited to available balance."
    )


@router.post("/withdraw", response_model=WithdrawalResponse)
async def withdraw_funds(
    req: WithdrawalRequestCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    withdrawal, ledger = await WalletService.request_withdrawal(db, user.id, req)
    await log_audit_event(
        db,
        action="WALLET_WITHDRAWAL_INITIATED",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        resource_type="withdrawal_request",
        resource_id=str(withdrawal.id),
        details={"amount": str(withdrawal.amount), "bank_info": req.bank_account_info}
    )
    return WithdrawalResponse(
        withdrawal_id=withdrawal.id,
        amount=withdrawal.amount,
        status=withdrawal.status,
        reference_id=withdrawal.reference_id,
        message="Withdrawal request initiated. Funds locked pending payout verification."
    )


@router.get("/transactions", response_model=List[LedgerEntryResponse])
async def get_ledger_transactions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet = await WalletService.get_or_create_wallet(db, user.id)
    return await WalletService.get_ledger_entries(db, wallet.id, limit=limit, offset=offset)


@router.get("/deposits", response_model=List[dict])
async def get_deposits(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet = await WalletService.get_or_create_wallet(db, user.id)
    res = await db.execute(
        select(DepositRequest)
        .where(DepositRequest.wallet_id == wallet.id)
        .order_by(DepositRequest.created_at.desc())
    )
    deposits = res.scalars().all()
    return [
        {
            "id": d.id,
            "amount": d.amount,
            "status": d.status,
            "reference_id": d.reference_id,
            "created_at": d.created_at
        }
        for d in deposits
    ]


@router.get("/withdrawals", response_model=List[dict])
async def get_withdrawals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet = await WalletService.get_or_create_wallet(db, user.id)
    res = await db.execute(
        select(WithdrawalRequest)
        .where(WithdrawalRequest.wallet_id == wallet.id)
        .order_by(WithdrawalRequest.created_at.desc())
    )
    withdrawals = res.scalars().all()
    return [
        {
            "id": w.id,
            "amount": w.amount,
            "status": w.status,
            "reference_id": w.reference_id,
            "bank_account_info": w.bank_account_info,
            "created_at": w.created_at
        }
        for w in withdrawals
    ]
