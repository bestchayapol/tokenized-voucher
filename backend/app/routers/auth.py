from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.deps import get_db, get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse, MeResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=MeResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.role not in ("issuer", "user", "merchant"):
        raise HTTPException(status_code=400, detail="invalid role")

    stmt = select(User).where(User.email == payload.email)
    if db.execute(stmt).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="email already exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return MeResponse(id=user.id, email=user.email, role=user.role)

@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form.username ใช้เป็น email ได้
    stmt = select(User).where(User.email == form.username)
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)

@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(id=user.id, email=user.email, role=user.role)