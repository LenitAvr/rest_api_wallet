import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import WalletDataBase
from schemas.operation import OperationType
from core.exceptions import WalletNotFoundError, InsufficientFundsError

class WalletService:
    async def get_wallet(self, db: AsyncSession, wallet_id: uuid.UUID) -> WalletDataBase:
        result = await db.execute(select(WalletDataBase).where(WalletDataBase.id == wallet_id))
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise WalletNotFoundError(f"Wallet with id {wallet_id} not found")
        return wallet

    async def update_balance(
        self,
        db: AsyncSession,
        wallet_id: uuid.UUID,
        amount: Decimal,
        operation_type: OperationType
    ) -> Decimal:
        async with db.begin():
            result = await db.execute(
                select(WalletDataBase).where(WalletDataBase.id == wallet_id).with_for_update()
            )
            wallet = result.scalar_one_or_none()
            if not wallet:
                raise WalletNotFoundError(f"Wallet with id {wallet_id} not found")

            if operation_type == OperationType.DEPOSIT:
                new_balance = wallet.balance + amount
            else:  
                if wallet.balance < amount:
                    raise InsufficientFundsError(
                        f"Insufficient funds. Available: {wallet.balance}, requested: {amount}"
                    )
                new_balance = wallet.balance - amount

            wallet.balance = new_balance
            await db.flush()

        return new_balance

    async def create_wallet(self, db: AsyncSession, initial_balance: Decimal = Decimal("0.00")) -> WalletDataBase:
        wallet = WalletDataBase(balance=initial_balance)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        return wallet

wallet_service = WalletService()