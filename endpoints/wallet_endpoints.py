import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.operation import OperationRequest, OperationResponse
from services.wallet_service import wallet_service
from core.exceptions import WalletNotFoundError, InsufficientFundsError

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    db: AsyncSession = Depends(get_db)
):
    wallet = await wallet_service.create_wallet(db, Decimal("0.00"))
    return {"wallet_id": str(wallet.id)}

@router.get("/{wallet_uuid}", response_model=OperationResponse)
async def get_balance(
    wallet_uuid: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):

    try:
        wallet = await wallet_service.get_wallet(db, wallet_uuid)
        return OperationResponse(balance=wallet.balance)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{wallet_uuid}/operation", response_model=OperationResponse)
async def perform_operation(
    wallet_uuid: uuid.UUID,
    operation: OperationRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        new_balance = await wallet_service.update_balance(
            db, wallet_uuid, operation.amount, operation.operation_type
        )
        return OperationResponse(balance=new_balance)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))