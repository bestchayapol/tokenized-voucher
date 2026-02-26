from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.voucher import Voucher, Balance
from app.models.ledger import LedgerEvent

def _ensure_voucher_exists(db: Session, voucher_id: int) -> None:
    if not db.get(Voucher, voucher_id):
        raise HTTPException(status_code=404, detail="voucher not found")

def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

def _get_or_create_balance(db: Session, user_id: int, voucher_id: int) -> Balance:
    stmt = select(Balance).where(Balance.user_id == user_id, Balance.voucher_id == voucher_id)
    bal = db.execute(stmt).scalar_one_or_none()
    if bal:
        return bal
    bal = Balance(user_id=user_id, voucher_id=voucher_id, balance=0)
    db.add(bal)
    db.flush()  # ensures bal.id is assigned
    return bal

def _ensure_ref_id_ununsed(db: Session, ref_id: str) -> None:
    # idemptency: if ref_id already exists, reject
    stmt = select(LedgerEvent.id).where(LedgerEvent.ref_id == ref_id)
    if db.execute(stmt).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="duplicate ref_id")

def issue(db: Session, issuer: User, voucher_id: int, to_user_id: int, amount: int, ref_id: str) -> None:
    if issuer.role != "issuer":
        raise HTTPException(status_code=403, detail="issuer role required")
    if to_user_id is None:
        raise HTTPException(status_code=400, detail="to_user_id is required for issue")
    
    _ensure_voucher_exists(db, voucher_id)
    _get_user(db, to_user_id)
    
    # Transaction block: balance update + ledger insert must be atomic
    with db.begin():
        _ensure_ref_id_ununsed(db, ref_id)
        
        bal = _get_or_create_balance(db, to_user_id, voucher_id)
        bal.balance += amount
        
        db.add(
            LedgerEvent(
                event_type="ISSUE",
                voucher_id=voucher_id,
                from_user_id=None,
                to_user_id=to_user_id,
                amount=amount,
                ref_id=ref_id,
                event_metadata={"by": issuer.id},
            )
        )

def transfer(db: Session, sender: User, voucher_id: int, to_user_id: int, amount: int, ref_id: str) -> None:
    if sender.role != "user":
        raise HTTPException(status_code=403, detail="user role required")
    if to_user_id is None:
        raise HTTPException(status_code=400, detail="to_user_id is required for transfer")
    
    _ensure_voucher_exists(db, voucher_id)
    _get_user(db, to_user_id)
    
    with db.begin():
        _ensure_ref_id_ununsed(db, ref_id)
        
        from_bal = _get_or_create_balance(db, sender.id, voucher_id)
        if from_bal.balance < amount:
            raise HTTPException(status_code=400, detail="insufficient balance")
        
        to_bal = _get_or_create_balance(db, to_user_id, voucher_id)
        
        from_bal.balance -= amount
        to_bal.balance += amount
        
        db.add(
            LedgerEvent(
                event_type="TRANSFER",
                voucher_id=voucher_id,
                from_user_id=sender.id,
                to_user_id=to_user_id,
                amount=amount,
                ref_id=ref_id,
                event_metadata=None,
            )
        )

def redeem(db: Session, user: User, voucher_id: int, merchant_user_id: int, amount: int, ref_id: str) -> None:
    if user.role != "user":
        raise HTTPException(status_code=403, detail="user role required")
    if merchant_user_id is None:
        raise HTTPException(status_code=400, detail="merchant_user_id is required for redeem")
    
    _ensure_voucher_exists(db, voucher_id)
    merchant = _get_user(db, merchant_user_id)
    if merchant.role != "merchant":
        raise HTTPException(status_code=400, detail="target user is not a merchant")
    
    with db.begin():
        _ensure_ref_id_ununsed(db, ref_id)
        
        user_bal = _get_or_create_balance(db, user.id, voucher_id)
        if user_bal.balance < amount:
            raise HTTPException(status_code=400, detail="insufficient balance")
        
        merchant_bal = _get_or_create_balance(db, merchant_user_id, voucher_id)
        
        user_bal.balance -= amount
        merchant_bal.balance += amount
        
        db.add(
            LedgerEvent(
                event_type="REDEEM",
                voucher_id=voucher_id,
                from_user_id=user.id,
                to_user_id=merchant_user_id,
                amount=amount,
                ref_id=ref_id,
                event_metadata={"merchant": merchant_user_id},
            )
        )