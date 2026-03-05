from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Float, Integer, Enum as SqlEnum
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime
import enum

class Base(AsyncAttrs, DeclarativeBase):
    pass

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    WAITING_FOR_APPROVE = "waiting_for_approve"
    APPROVED = "approved"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELED = "canceled"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String)
    vnd_amount: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(SqlEnum(TransactionStatus), default=TransactionStatus.PENDING)
    pin_code: Mapped[str] = mapped_column(String, nullable=True)
    
    # НОВОЕ ПОЛЕ: ID сообщения с кнопкой отмены
    cancel_message_id: Mapped[int] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)