from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import auth

router = APIRouter(prefix="/bias", tags=["Bias"])


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    tick_volume: int

class BiasComputeRequest(BaseModel):
    symbol: str
    timeframe: str
    historical_data: List[Candle]  # typical structure you provided


class BiasResult(BaseModel):
    symbol: str
    timeframe: str
    bias: str                 # "bullish" | "bearish" | "neutral"
    confidence: int           # 0-100
    reason: str
    computed_at: str


def simple_trend_bias(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simple heuristic bias:
    - compute last N close changes, sma slope, recent higher highs / higher lows.
    - return { bias, confidence, reason }
    This is intentionally simple and deterministic.
    """
    n = len(candles)
    if n < 3:
        return {"bias": "neutral", "confidence": 40, "reason": "insufficient data"}

    closes = [c["close"] for c in candles]
    # slope over entire window
    slope = (closes[-1] - closes[0]) / max(1, n)
    # recent direction using last 3 closes
    last_changes = closes[-3:]
    rise_count = sum(1 for i in range(1, len(last_changes)) if last_changes[i] > last_changes[i-1])
    fall_count = sum(1 for i in range(1, len(last_changes)) if last_changes[i] < last_changes[i-1])

    # HH/HL vs LL/LH detection
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    hh = highs[-1] > max(highs[:-1])
    ll = lows[-1] < min(lows[:-1])

    confidence = 50
    if slope > 0 and rise_count >= 2:
        bias = "bullish"
        confidence = min(95, 60 + int(abs(slope) * 1000))
        reason = "Upward slope and recent higher closes"
    elif slope < 0 and fall_count >= 2:
        bias = "bearish"
        confidence = min(95, 60 + int(abs(slope) * 1000))
        reason = "Downward slope and recent lower closes"
    else:
        bias = "neutral"
        confidence = 40
        reason = "No clear slope; mixed closes"

    # strengthen confidence if HH/HL or LL/LH obvious
    if bias == "bullish" and hh:
        confidence = min(100, confidence + 10)
        reason += "; detected higher high"
    if bias == "bearish" and ll:
        confidence = min(100, confidence + 10)
        reason += "; detected lower low"

    return {"bias": bias, "confidence": confidence, "reason": reason}


@router.post("/compute", response_model=BiasResult)
def compute_bias(payload: BiasComputeRequest, user=Depends(auth.get_current_user)):
    """
    Compute bias for a timeframe using a lightweight deterministic heuristic.
    This provides a fast, reproducible bias for H1/H4/D1.
    """
    try:
        candles = [c.dict() for c in payload.historical_data]
        result = simple_trend_bias(candles)
        return {
            "symbol": payload.symbol,
            "timeframe": payload.timeframe,
            "bias": result["bias"],
            "confidence": int(result["confidence"]),
            "reason": result["reason"],
            "computed_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
