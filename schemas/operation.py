from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal

class OperationType(str, Enum):
    DEPOSIT = 'DEPOSIT'
    WITHDRAW = 'WITHDRAW'

class OperationRequest(BaseModel):
    operation_type: OperationType
    amount: Decimal = Field(..., gt=0, description='Поле должно быть больше нуля')

class OperationResponse(BaseModel):
    balance: Decimal
