import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.errors import AppError, InsufficientFundsError, ResourceNotFoundError
from app.models.wallet import Wallet, LedgerEntry, DepositRequest, WithdrawalRequest
from app.schemas.wallet import DepositRequestCreate, WithdrawalRequestCreate


class WalletService:
    @staticmethod
    async def get_or_create_wallet(db: AsyncSession, user_id: uuid.UUID) -> Wallet:
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        wallet = result.scalar_one_or_none()
        if not wallet:
            wallet = Wallet(
                user_id=user_id,
                available_balance=Decimal("0.00"),
                locked_balance=Decimal("0.00"),
                currency="INR"
            )
            db.add(wallet)
            await db.commit()
            await db.refresh(wallet)
        return wallet

    @staticmethod
    async def process_deposit(
        db: AsyncSession,
        user_id: uuid.UUID,
        req: DepositRequestCreate,
        reference_id: Optional[str] = None
    ) -> Tuple[DepositRequest, LedgerEntry]:
        wallet = await WalletService.get_or_create_wallet(db, user_id)

        # Check idempotency key to prevent duplicate money movement
        existing_deposit = await db.execute(
            select(DepositRequest).where(DepositRequest.idempotency_key == req.idempotency_key)
        )
        if existing_deposit.scalar_one_or_none():
            raise AppError(code="DUPLICATE_IDEMPOTENCY_KEY", message="This deposit request has already been processed")

        deposit_amt = Decimal(str(req.amount))
        if deposit_amt <= Decimal("0.00"):
            raise AppError(code="INVALID_AMOUNT", message="Deposit amount must be strictly positive")

        # 1. Create DepositRequest
        deposit = DepositRequest(
            wallet_id=wallet.id,
            amount=deposit_amt,
            currency="INR",
            idempotency_key=req.idempotency_key,
            payment_provider=req.payment_method,
            status="COMPLETED",
            reference_id=reference_id or f"DEP-{uuid.uuid4().hex[:10].upper()}"
        )
        db.add(deposit)

        # 2. Update wallet balance
        new_available = Decimal(str(wallet.available_balance)) + deposit_amt
        wallet.available_balance = new_available

        # 3. Create immutable ledger entry
        ledger = LedgerEntry(
            wallet_id=wallet.id,
            reference=deposit.reference_id,
            entry_type="DEPOSIT",
            direction="CREDIT",
            amount=deposit_amt,
            balance_after=new_available,
            status="POSTED",
            description=f"Fund deposit via {req.payment_method}",
            metadata_json={"idempotency_key": req.idempotency_key, "provider": req.payment_method}
        )
        db.add(ledger)

        await db.commit()
        await db.refresh(deposit)
        await db.refresh(ledger)
        return deposit, ledger

    @staticmethod
    async def request_withdrawal(
        db: AsyncSession,
        user_id: uuid.UUID,
        req: WithdrawalRequestCreate
    ) -> Tuple[WithdrawalRequest, LedgerEntry]:
        wallet = await WalletService.get_or_create_wallet(db, user_id)
        withdraw_amt = Decimal(str(req.amount))

        if withdraw_amt <= Decimal("0.00"):
            raise AppError(code="INVALID_AMOUNT", message="Withdrawal amount must be strictly positive")

        available = Decimal(str(wallet.available_balance))
        if available < withdraw_amt:
            raise InsufficientFundsError(
                f"Requested withdrawal ₹{withdraw_amt} exceeds available balance ₹{available}"
            )

        # 1. Lock funds immediately (Available -> Locked)
        wallet.available_balance = available - withdraw_amt
        wallet.locked_balance = Decimal(str(wallet.locked_balance)) + withdraw_amt

        # 2. Create WithdrawalRequest
        ref_id = f"WTH-{uuid.uuid4().hex[:10].upper()}"
        withdrawal = WithdrawalRequest(
            wallet_id=wallet.id,
            amount=withdraw_amt,
            bank_account_info=req.bank_account_info,
            status="PENDING",
            reference_id=ref_id
        )
        db.add(withdrawal)

        # 3. Record lock in Ledger
        ledger = LedgerEntry(
            wallet_id=wallet.id,
            reference=ref_id,
            entry_type="WITHDRAWAL_LOCK",
            direction="DEBIT",
            amount=withdraw_amt,
            balance_after=wallet.available_balance,
            status="POSTED",
            description=f"Funds held for withdrawal to {req.bank_account_info}",
            metadata_json={"withdrawal_ref": ref_id}
        )
        db.add(ledger)

        await db.commit()
        await db.refresh(withdrawal)
        await db.refresh(ledger)
        return withdrawal, ledger

    @staticmethod
    async def finalize_withdrawal(
        db: AsyncSession,
        withdrawal_id: uuid.UUID,
        success: bool = True
    ) -> WithdrawalRequest:
        result = await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id))
        withdrawal = result.scalar_one_or_none()
        if not withdrawal:
            raise ResourceNotFoundError("WithdrawalRequest", withdrawal_id)

        if withdrawal.status != "PENDING":
            raise AppError(code="INVALID_STATUS", message=f"Withdrawal already in state {withdrawal.status}")

        wallet = await db.get(Wallet, withdrawal.wallet_id)
        withdraw_amt = Decimal(str(withdrawal.amount))

        if success:
            # Payout succeeded: remove from locked balance permanently
            wallet.locked_balance = Decimal(str(wallet.locked_balance)) - withdraw_amt
            withdrawal.status = "PROCESSED"

            ledger = LedgerEntry(
                wallet_id=wallet.id,
                reference=f"FIN-{withdrawal.reference_id}",
                entry_type="WITHDRAWAL_FINAL",
                direction="DEBIT",
                amount=withdraw_amt,
                balance_after=wallet.available_balance,
                status="POSTED",
                description="Withdrawal payout completed successfully",
                metadata_json={"status": "PROCESSED"}
            )
            db.add(ledger)
        else:
            # Payout failed: restore locked funds to available balance
            wallet.locked_balance = Decimal(str(wallet.locked_balance)) - withdraw_amt
            wallet.available_balance = Decimal(str(wallet.available_balance)) + withdraw_amt
            withdrawal.status = "REJECTED"

            ledger = LedgerEntry(
                wallet_id=wallet.id,
                reference=f"REV-{withdrawal.reference_id}",
                entry_type="WITHDRAWAL_REVERT",
                direction="CREDIT",
                amount=withdraw_amt,
                balance_after=wallet.available_balance,
                status="POSTED",
                description="Withdrawal payout failed; funds unlocked to available balance",
                metadata_json={"status": "REJECTED"}
            )
            db.add(ledger)

        await db.commit()
        await db.refresh(withdrawal)
        return withdrawal

    @staticmethod
    async def get_ledger_entries(db: AsyncSession, wallet_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[LedgerEntry]:
        result = await db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.wallet_id == wallet_id)
            .order_by(LedgerEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
