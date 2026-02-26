from datetime import datetime
from pydantic import BaseModel

class LedgerEventResponse(BaseModel):
    id: int
    event_type: str
    voucher_id: int
    from_user_id: int | None
    to_user_id: int | None
    amount: int
    ref_id: str
    created_at: datetime