from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.routers.auth import router as auth_router

app = FastAPI(title="Tokenized Voucher API")

app.include_router(auth_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_ok": True, "result": result}