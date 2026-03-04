from sqlalchemy import BigInteger, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import Enum as PyEnum

from database.db import Base


class TransactionStatus(PyEnum):
    PENDING = "pending"
    WAITING_FOR_APPROVE = "waiting_for_approve"
    APPROVED = "approved"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELED = "canceled"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    amount: Mapped[float]
    currency: Mapped[str] = mapped_column(String(10))
    vnd_amount: Mapped[float]
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        default=TransactionStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
