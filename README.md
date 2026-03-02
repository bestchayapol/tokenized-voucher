# Tokenized Voucher (Mini Tokenization) 

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

## Day 4 — Auth (Register / Login) + JWT + Roles (Swagger Ready)

Day 4 goal: implement **authentication** (register/login) with **JWT bearer tokens**, and support 3 roles:
- `issuer`
- `user`
- `merchant`

This enables:
- Register users
- Login to receive `access_token`
- Use Swagger **Authorize** to call protected endpoints
- Prepare role-based access for Day 5 (e.g., issuer-only actions)

---

###  What’s done (Day 4 checklist)
- [x] POST `/auth/register` create user (email/password/role)
- [x] POST `/auth/login` returns JWT access token
- [x] GET `/auth/me` returns current user (requires Bearer token)
- [x] `get_current_user()` to decode JWT and load user from DB
- [x] `require_role()` helper for role-based access (used in later days)
- [x] Swagger Authorize flow works

---

## Requirements (Auth)

Make sure these packages exist in `backend/requirements.txt`:
- `python-jose[cryptography]` (JWT)
- `passlib[bcrypt]` (password hashing)
- `python-multipart` (required for OAuth2 password-form login)

> If `python-multipart` is missing, `/auth/login` will fail because the password-flow expects **form-data**.

After updating requirements:
```powershell
docker compose up --build -d
```
## Environment (.env)

Add these to backend/.env:

```env
JWT_SECRET=<your_random_secret>
ACCESS_TOKEN_EXPIRE_MINUTES=60
```
Generate a secret
```powershell
openssl rand -hex 32
```
> Do NOT commit .env to GitHub.   

## API Endpoints
### 1) Register (Public)

POST /auth/register

Request body example:
```json
{
  "email": "johndoe@hotmail.com",
  "password": "secret",
  "role": "user"
}
```
### 2) Login (Public)

OAuth2 password flow uses form-data fields:

        username (we use email here)
        password

In Swagger, click Try it out and fill:

        username: johndoe@hotmail.com
        password: secret

Response:
```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```
### 3) Me (Protected)

GET /auth/me

Requires Bearer token.

## Swagger Demo (How to test quickly)
1.    Open Swagger:
  
           http://localhost:8000/docs

3.    Register 3 accounts:

          issuer: role="issuer"
          user: role="user"
          merchant: role="merchant"

3.    Login as any user:

          POST /auth/login
          Copy access_token

4.    Click Authorize (top-right in Swagger):

          Paste:
          Bearer <access_token>

5.    Call protected endpoint:

          GET /auth/me → should return your user info

## Notes/Common Issues

### A) 401 Unauthorized on /auth/register

Register should be public. If it returns 401:
    •    Make sure /auth/register is NOT protected by Depends(get_current_user)
    •    Avoid setting router-wide dependencies that require auth.

### B) 500 Internal Server Error on register (DB constraint)

If DB has extra NOT NULL columns (e.g., username), register may fail.
Fix by aligning the model/schema and applying migrations (Day 3).

### C) bcrypt password length limit (72 bytes)

bcrypt is designed for passwords up to 72 bytes.
For this project, keep passwords reasonably short (or validate max length).

## Useful Commands

View backend logs:
```powershell
docker compose logs -f backend --tail=200
```
View DB logs:
```powershell
docker compose logs -f db --tail=200
```
Restart all:
```powershell
docker compose down
docker compose up --build -d
```
     
## Day 5 — Voucher + ISSUE / TRANSFER / REDEEM + Ledger (Swagger Demo)

Day 5 goal: implement core token flows for **Tokenized Voucher**:
- Create Voucher (issuer-only)
- Issue (issuer → user)
- Transfer (user → user)
- Redeem (user → merchant)
- Ledger (audit trail for every transaction)
- Idempotency (prevent duplicate transaction using `ref_id`)

> Key idea: every transaction must update balances + write ledger event atomically (in one DB transaction).

---

### ✅ Done (Day 5 checklist)
- [x] POST `/vouchers` (issuer-only) create voucher
- [x] GET `/vouchers` list vouchers (auth required)
- [x] GET `/vouchers/{id}/balance/me` check own balance
- [x] POST `/vouchers/{id}/issue` (issuer → user)
- [x] POST `/vouchers/{id}/transfer` (user → user)
- [x] POST `/vouchers/{id}/redeem` (user → merchant)
- [x] GET `/ledger/vouchers/{id}?limit=&offset=` list ledger events
- [x] `ref_id` idempotency (duplicate → 409)

---

## Swagger Step-by-Step Demo (Day 5)

> Open Swagger:
- If compose maps `18000:8000` → http://localhost:18000/docs
- If compose maps `8000:8000` → http://localhost:8000/docs

### 1) Register 3 roles (one-time)
POST `/auth/register`:
- issuer: role="issuer"
- user1: role="user"
- merchant: role="merchant"

### 2) Login issuer + Authorize
POST `/auth/login` (form-data):
- username = issuer email
- password = secret

Copy `access_token` → Swagger **Authorize**:
`Bearer <issuer_token>`

Confirm: GET `/auth/me` returns role `"issuer"`.

### 3) Create Voucher (issuer-only)
POST `/vouchers`
```json
{ "code": "FOOD-2026", "name": "Food Voucher 2026" }
```
Save voucher_id from response.

### 4) Issue to user1 (issuer -> user)
POST `/vouchers/{voucher_id}/issue`
```json
{ "to_user_id": <user1_id>, "amount": 100, "ref_id": "<new-uuid>" }
```

### 5) Login user1 + Authorize (switch token)
POST `/auth/login` for user1 -> Authorize with user1 token
Confirm: GET `/auth/me` role "user".

### 6) Check balance (user1)

GET `/vouchers/{voucher_id}/balance/me` → should show balance 100

### 7) Redeem to merchant (user -> merchant)

POST `/vouchers{voucher_id}/redeem

```json
{ "merchant_user_id": <merchant_id>, "amount": 50, "ref_id": "<new-uuid>" }
```

### 8) Ledger (audit trail)

GET `/ledger/vouchers/{voucher_id}?limit=20&offset=0`
You should see events like ISSUE and REDEEM (and TRANSFER if you tested it).

### 9) Idempotency test

Send the same request again with the same ref_id → should return 409 Conflict.

### Useful commands
```powershell
docker compose logs -f backend --tail=200
docker compose exec db psql -U app -d voucherdb -c "\dt"
```

## Day 6 — Ledger API + Pagination + Stronger Idempotency

Day 6 goal: make the system more **production-like** by improving:
- **Ledger API** (pagination with `limit/offset`)
- **Idempotency** (duplicate `ref_id` returns **409**, not 500)
- **Validation** (use UUID for `ref_id`)

---

### :white_check_mark: Done (Day 6 checklist)
- [x] Ledger endpoint supports pagination:
  - GET `/ledger/vouchers/{voucher_id}?limit=20&offset=0`
  - limit has min/max guard (e.g. 1–100)
- [x] `ref_id` is validated as UUID at request schema level
- [x] Idempotency is stronger:
  - duplicate `ref_id` returns **409 Conflict**
  - handled safely even under race conditions (catch DB `IntegrityError`)
- [x] Verified in Swagger:
  - ledger returns correct events
  - same `ref_id` cannot be processed twice

---

## How to run
```powershell
docker compose up --build -d
```
Swagger:
    • http://localhost:8000/docs
    (or use your mapped port เช่น http://localhost:18000/docs) 
Ledger API

Endpoint

GET /ledger/vouchers/{voucher_id}

Query params
    •    limit (default 20, min 1, max 100)
    •    offset (default 0)

Example:
```
GET /ledger/vouchers/1?limit=2&offset=0
GET /ledger/vouchers/1?limit=2&offset=2
```
Expected response fields (per event):
    •    event_type (ISSUE/TRANSFER/REDEEM)
    •    from_user_id, to_user_id
    •    amount
    •    ref_id
    •    created_at
### Idempotency rule (ref_id)
All state-changing endpoints must include ref_id:
    •    POST /vouchers/{id}/issue
    •    POST /vouchers/{id}/transfer
    •    POST /vouchers/{id}/redeem

Rules:
    
1. If ref_id has never been used → process normally (200)
2. If ref_id is reused → return 409 Conflict (no double-spend)

ref_id is validated as UUID by schema, so bad formats will fail early (422).
### Swagger Demo (Day 6)
1. Login as issuer → create voucher → issue to user (use a new UUID for ref_id)
2. Login as user → redeem to merchant (use a new UUID for ref_id)
3. Check ledger:
    • GET /ledger/vouchers/{voucher_id}?limit=20&offset=0
4. Test idempotency:
    • Send the same redeem request again with the same ref_id
    • Expected: 409 Conflict

Quick DB checks (optional)
List balances:
```docker
docker compose exec db psql -U app -d voucherdb -c "select user_id,voucher_id,balance from balances order by user_id,voucher_id;"
```
Latest ledger events:
```docker
docker compose exec db psql -U app -d voucherdb -c "select id,event_type,voucher_id,from_user_id,to_user_id,amount,ref_id,created_at from ledger_events order by id desc limit 20;"
```
Backend logs:
```docker
docker compose logs -f backend --tail=200
 ```


## Day 7 — Tests + GitHub Actions CI + README/Demo Script

Day 7 goal: add automated testing, CI pipeline, and clear demo instructions.

### ✅ Checklist
- [x] Pytest tests for main flows
- [x] GitHub Actions CI runs tests on push
- [x] Updated README with demo/test steps

---

### How to run (local or CI)

1. **Start all services:**
  ```powershell
  docker compose up --build -d
  ```

2. **Open Swagger UI:**
  - [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Run tests:**
  ```powershell
  docker compose exec backend pytest -q
  ```

---

### Demo steps (Day 5 flows)

1. **Register 3 roles:**
  - POST `/auth/register` for:
    - issuer: role="issuer"
    - user1: role="user"
    - merchant: role="merchant"

2. **Login as issuer + Authorize:**
  - POST `/auth/login` (form-data):
    - username = issuer email
    - password = secret
  - Copy `access_token` → Swagger **Authorize**
  - Confirm: GET `/auth/me` returns role "issuer"

3. **Create Voucher (issuer-only):**
  - POST `/vouchers`
    ```json
    { "code": "FOOD-2026", "name": "Food Voucher 2026" }
    ```
  - Save voucher_id from response

4. **Issue to user1 (issuer → user):**
  - POST `/vouchers/{voucher_id}/issue`
    ```json
    { "to_user_id": <user1_id>, "amount": 100, "ref_id": "<new-uuid>" }
    ```

5. **Login as user1 + Authorize:**
  - POST `/auth/login` for user1 → Authorize with user1 token
  - Confirm: GET `/auth/me` role "user"

6. **Check balance (user1):**
  - GET `/vouchers/{voucher_id}/balance/me` → should show balance 100

7. **Redeem to merchant (user → merchant):**
  - POST `/vouchers/{voucher_id}/redeem`
    ```json
    { "merchant_user_id": <merchant_id>, "amount": 50, "ref_id": "<new-uuid>" }
    ```

8. **Ledger (audit trail):**
  - GET `/ledger/vouchers/{voucher_id}?limit=20&offset=0`
  - You should see events like ISSUE and REDEEM (and TRANSFER if you tested it)

9. **Idempotency test:**
  - Send the same request again with the same ref_id → should return 409 Conflict

---

### CI: GitHub Actions

- On every push, GitHub Actions will:
  - Build the backend image
  - Start services with docker compose
  - Run all tests with pytest
  - Fail if any test fails

See `.github/workflows/` for pipeline config.


