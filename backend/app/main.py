from fastapi import FastAPI

app = FastAPI(title="Tokenized Voucher API")

@app.get("/health")

def health():
    return {"status": "ok"}