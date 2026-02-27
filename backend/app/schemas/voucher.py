from pydantic import BaseModel, Field
from uuid import UUID

class CreateVoucherRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    
class VoucherResponse(BaseModel):
    id: int
    code: str
    name: str

class TxRequest(BaseModel):
    # ISSUE / TRANSFER ใช้ to_user_id
    to_user_id: int | None = None
    
    # REDEEM ใข้ merchant_user_id
    merchant_user_id: int | None = None
    
    amount: int = Field(gt=0)   # > 0
    ref_id: UUID    # validate format