from datetime import datetime
from app.db.base import Base
from sqlalchemy import String, DateTime, UniqueConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

class Voucher(Base):
    __tablename__ = "vouchers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
class Balance(Base):
    __tablename__ = "balances"
    __table_args__ = (
        # Ensure a user can only have one balance record per voucher
        UniqueConstraint('user_id', 'voucher_id', name='uq_balance_user_voucher'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    voucher_id: Mapped[int] = mapped_column(ForeignKey("vouchers.id"), nullable=False)
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)