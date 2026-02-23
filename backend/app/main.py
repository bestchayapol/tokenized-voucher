from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db

app = FastAPI(title="Tokenized Voucher API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    # query ง่ายๆ เพื่อเช็คการเชื่อมต่อกับฐานข้อมูล
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"status": "ok", "db": "connected", "db_ok": True, "result": result}
    except Exception as e:
        return {"status": "error", "db": "disconnected", "error": str(e), "db_ok": False, "result": None}