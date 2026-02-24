from datetime import datetime
from app.db.base import Base
from sqlalchemy import String, DateTime, UniqueConstraint, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

class LedgerEvent(Base):
    __tablename__ = "ledger_events"
    __table_args__ = (
        # Ensure ref_id is unique to prevent duplicate events 
        UniqueConstraint('ref_id', name='uq_ledger_event_ref_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ISSUE/TRANSFER/REDEEM
    voucher_id: Mapped[int] = mapped_column(ForeignKey("vouchers.id"), nullable=False)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    ref_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)