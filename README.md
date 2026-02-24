# Tokenized Voucher (Mini Tokenization) 
Mini Project for applicant in full stack at BOT

## Day 1 — FastAPI (Local Dev / Windows PowerShell)
### :white_check_mark: Checklist
- [x] Create project structure: `tokenized-voucher/backend/app`
- [x] Create + activate venv
- [x] Install dependencies
- [x] Run FastAPI with auto-reload
- [x] Open `/health` and `/docs`
- [x] Commit + push to GitHub

### PowerShell 
```powershell
cd backend
python -m venv .venv
..venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
### requirement.txt 
``` txt
fastapi
uvicorn[standard]
```
### app/main.py 
``` python
from fastapi import FastAPI

app = FastAPI(title="Tokenized Voucher API")

@app.get("/health")
def health():
    return {"status": "ok"}
```
### Expected JSON 
``` 
{"status": "ok"}
```

## Day 2— Docker Compose + PostgreSQL + Connect DB (Windows)

### ✅ Checklist
- [x] Docker Desktop + docker compose works
- [x] Add docker-compose.yml (db + backend)
- [x] Add backend Dockerfile
- [x] Add SQLAlchemy + PostgreSQL driver
- [x] Add .env with DATABASE_URL
- [x] Add DB session + get_db() dependency
- [x] Add /db-check endpoint
- [x] docker compose up --build works
- [x] /db-check returns result = 1
   
### docker-compose.yml 
Note: 15432:5432 avoids port conflict on Windows. Container still listens on 5432 internally.
```yml
services:
  db:
    image: postgres:lastest
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: voucherdb
    ports:
      - "15432:5432"
    volumes:
      - pgdata:/var/lib/postgresql

  backend:
    build: ./backend
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    depends_on:
      - db

volumes:
  pgdata:
```

### backend/Dockerfile 
```Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### backend/requirements.txt 
```txt
fastapi
uvicorn[standard]
sqlalchemy>=2.0
psycopg2-binary
python-dotenv
```

### backend/.env.example 
```env
DATABASE_URL=postgresql+psycopg2://app:app@db:5432/voucherdb
```

### PowerShell 
``` powershell
# from project root
Copy-Item backend\.env.example backend\.env

docker compose up --build
```

### backend/app/db/session.py
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

### backend/app/core/deps.py 
```python
from app.db.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### backend/app/main.py
```python
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
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_ok": True, "result": result}
```

### Verify in browser
  - http://localhost:8000/health
  - http://localhost:8000/docs
  - http://localhost:8000/db-check

### Expected JSON 
```json
{"status":"ok","db":"connected","db_ok":true,"result":1}
```

### Useful commands
```powershell
# stop containers
docker compose down

# reset DB volume (DANGER: deletes DB data)
docker compose down -v

# view logs
docker compose logs -f db
docker compose logs -f backend
```

## Day 3 — Models + Alembic Migration (Run inside backend container)

Day 3 goal: define database schema using **SQLAlchemy models** and generate/apply **Alembic migrations** inside the running backend container.

### :white_check_mark: Done (Day 3 checklist)
- [x] Added SQLAlchemy Base (DeclarativeBase)
- [x] Created models: `users`, `vouchers`, `balances`, `ledger_events`
- [x] Initialized Alembic in backend container
- [x] Configured `alembic/env.py` to:
  - read `DATABASE_URL` from environment
  - use `target_metadata = Base.metadata`
  - import models before autogenerate
- [x] Generated migration script with `--autogenerate`
- [x] Applied migration with `upgrade head`
- [x] Verified tables exist in PostgreSQL

> Note: In SQLAlchemy Declarative API, the attribute name `metadata` is reserved.  
> The `ledger_events` model uses a safe attribute name (e.g. `event_metadata`) mapped to DB column `"metadata"`.

---

### Commands (run in PowerShell)

> `docker compose exec` runs a command inside a running service container.  
> Reference: Docker Compose exec docs.

1) Start containers (if not running):
```powershell
docker compose up -d
```

### Create migration script (autogenerate):
```powershell
docker compose exec backend alembic revision --autogenerate -m "init tables"
```

### Apply migration:
```powershell
docker compose exec backend alembic upgrade head
```

### Verify tables in Postgres:
```docker compose exec db psql -U app -d voucherdb -c "\dt"```

### Expected tables (example):
    - users
    - vouchers
    - balances
    - ledger_events
    - alembic_version