from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User

from app.schemas.voucher import VoucherResponse, CreateVoucherRequest, TxRequest
from app.services.token_service import issue as svc_issue, transfer as svc_transfer, redeem as svc_redeem
from app.models.voucher import Voucher, Balance
from app.core.deps import get_db, require_role, get_current_user

router = APIRouter(prefix="/vouchers", tags=["vouchers"])

@router.post("", response_model=VoucherResponse)
def create_voucher(
    pay_load: CreateVoucherRequest,
    db: Session = Depends(get_db),
    issuer: User = Depends(require_role("issuer")),
):
    v = Voucher(
        name=pay_load.name,
        code=pay_load.code,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return VoucherResponse(id=v.id, code=v.code, name=v.name)

@router.get("", response_model=list[VoucherResponse])
def list_vouchers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.execute(select(Voucher).order_by(Voucher.id.asc())).scalars().all()
    return [VoucherResponse(id=v.id, code=v.code, name=v.name) for v in rows]

@router.get("/{voucher_id}/balance/me")
def my_balance(
    voucher_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Balance).where(Balance.voucher_id == voucher_id, Balance.user_id == user.id)
    bal = db.execute(stmt).scalar_one_or_none()
    return {"voucher_id": voucher_id, "user_id": user.id, "balance": bal.balance if bal else 0}

@router.post("/{voucher_id}/issue")
def issue(
    voucher_id: int,
    payload: TxRequest,
    db: Session = Depends(get_db),
    issuer: User = Depends(require_role("issuer")),
):
    svc_issue(db, issuer, voucher_id, payload.to_user_id, payload.amount, payload.ref_id)
    return {"ok": True}

@router.post("/{voucher_id}/transfer")
def transfer(
    voucher_id: int,
    payload: TxRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc_transfer(db, user, voucher_id, payload.to_user_id, payload.amount, payload.ref_id)
    return {"ok": True}

@router.post("/{voucher_id}/redeem")
def redeem(
    voucher_id: int,
    payload: TxRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc_redeem(db, user, voucher_id, payload.merchant_user_id ,payload.amount, payload.ref_id)
    return {"ok": True}