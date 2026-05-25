from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid, hashlib

app = FastAPI(title="Fintech Payment API (Simulated)", version="1.0.0")

class LoginRequest(BaseModel):
    username: str; password: str; device_id: str = "unknown"

class TransferRequest(BaseModel):
    from_account: str; to_account: str; amount: float; currency: str = "VND"; otp: str

class BalanceRequest(BaseModel):
    account_id: str; token: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/login")
def login(req: LoginRequest):
    token = hashlib.sha256(f"{req.username}:{req.password}:{datetime.utcnow().timestamp()}".encode()).hexdigest()[:32]
    return {"status": "success", "token": token, "expires_in": 3600, "user_id": str(uuid.uuid4()), "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/transfer")
def transfer(req: TransferRequest):
    if req.amount <= 0: raise HTTPException(400, "Invalid amount")
    if len(req.otp) != 6: raise HTTPException(400, "Invalid OTP")
    return {"status": "success", "transaction_id": f"TXN-{uuid.uuid4().hex[:12].upper()}", "amount": req.amount, "currency": req.currency, "fee": round(req.amount*0.001,2), "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/balance")
def get_balance(req: BalanceRequest):
    return {"account_id": req.account_id[:4]+"****"+req.account_id[-4:], "available_balance": 15250000.50, "currency": "VND", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/exchange-rates")
def exchange_rates():
    return {"rates": {"USD_VND": 25430.00, "EUR_VND": 27120.50, "GBP_VND": 31850.75}, "timestamp": datetime.utcnow().isoformat()}
