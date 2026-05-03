import uuid

from sqlalchemy import Column, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from db.session import Base


class WalletDataBase(Base):
    __tablename__ = 'wallets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)

