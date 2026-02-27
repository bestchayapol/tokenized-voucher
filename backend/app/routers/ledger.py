from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.ledger import LedgerEvent
from app.schemas.ledger import LedgerEventResponse
from app.core.deps import get_db, get_current_user

router = APIRouter(prefix="/ledger", tags=["ledger"])

MAX_LIMIT = 100

@router.get("/vouchers/{voucher_id}", response_model=list[LedgerEventResponse])
def voucher_ledger(
    voucher_id: int,
    limit: int = Query(20, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),    
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(LedgerEvent)
        .where(LedgerEvent.voucher_id == voucher_id)
        .order_by(LedgerEvent.id.desc())
        .limit(limit)
        .offset(offset)
    )
    events = db.execute(stmt).scalars().all()
    return [
        LedgerEventResponse(
            id=e.id,
            event_type=e.event_type,
            voucher_id=e.voucher_id,
            from_user_id=e.from_user_id,
            to_user_id=e.to_user_id,
            amount=e.amount,
            ref_id=e.ref_id,
            created_at=e.created_at,
        )
        for e in events
    ]