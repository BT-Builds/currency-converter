import os
import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict

app = FastAPI(
    title="Currency Converter API",
    description="Convert currency with realistic e-commerce markup for accurate pricing",
    version="1.0.0"
)
# === BT Builds Standard Middleware (auto-injected) ===
from fastapi.middleware.cors import CORSMiddleware as _BTCors
app.add_middleware(_BTCors, allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"], expose_headers=["X-RateLimit-Limit","X-RateLimit-Remaining","X-RateLimit-Reset"])

@app.middleware("http")
async def _bt_add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "btbuilds"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


API_KEY = os.environ.get("API_KEY", "dev-key-change-in-production")
RATE_LIMIT = 100

def verify_api_key(authorization: Optional[str] = None):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.replace("Bearer ", "")
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token

class ConvertRequest(BaseModel):
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code (USD, EUR, etc.)")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code (USD, EUR, etc.)")
    amount: float = Field(..., gt=0, description="Amount to convert")
    fee_type: str = Field("mid", description="Fee type: mid, paypal, stripe, wise")

class ConvertResponse(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    fee_type: str
    exchange_rate: float
    markup_percent: float
    timestamp: str

FEE_MARKS = {
    "mid": 0.0,
    "paypal": 4.0,
    "stripe": 2.9,
    "wise": 0.5
}

def get_exchange_rate(from_curr: str, to_curr: str) -> float:
    url = f"https://api.exchangerate-api.com/v4/latest/{from_curr.upper()}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        if to_curr.upper() not in rates:
            raise HTTPException(status_code=400, detail=f"Currency {to_curr} not supported")
        return rates[to_curr.upper()]
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Exchange rate service unavailable: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "currency-converter"}

@app.post("/convert")
async def convert_currency(req: ConvertRequest, _: str = Depends(verify_api_key)):
    rate = get_exchange_rate(req.from_currency, req.to_currency)
    markup = FEE_MARKS.get(req.fee_type, 0.0)
    adjusted_rate = rate * (1 - markup / 100)
    converted = req.amount * adjusted_rate
    
    return ConvertResponse(
        from_currency=req.from_currency.upper(),
        to_currency=req.to_currency.upper(),
        amount=req.amount,
        converted_amount=round(converted, 4),
        fee_type=req.fee_type,
        exchange_rate=rate,
        markup_percent=markup,
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/currencies")
async def list_currencies(_: str = Depends(verify_api_key)):
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {"currencies": sorted(data.get("rates", {}).keys()), "base": "USD", "count": len(data.get("rates", {}))}
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Exchange rate service unavailable")

@app.get("/fee-types")
async def list_fee_types():
    return {"fee_types": list(FEE_MARKS.keys()), "markups": FEE_MARKS}

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    pass
