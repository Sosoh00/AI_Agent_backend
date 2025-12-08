from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from services.ai_services import ai_service
import auth

router = APIRouter(prefix="/ai", tags=["AI"])


# ---------- Request Schema ----------

class TimeframeData(BaseModel):
    symbol: str
    timeframe: str
    historical_data: List[Dict[str, Any]]


class AIRequest(BaseModel):
    symbol: str
    timeframes: Dict[str, TimeframeData]
    sentiment: Dict[str, Any]
    journal_recent: List[Dict[str, Any]] = []
    backtest_profile: Dict[str, Any] = {}


# ---------- Endpoint ----------

@router.post("/decision")
async def ai_decision(payload: AIRequest, user: dict = Depends(auth.get_current_user)):
    """
    Takes full market data (M5–D1 + sentiment + journal)
    Sends to OpenAI
    Returns trade decision in strict JSON format.
    """

    try:
        model_payload = await ai_service.build_model_payload(
            symbol=payload.symbol,
            timeframe_data={k: v.dict() for k, v in payload.timeframes.items()},
            sentiment=payload.sentiment,
            journal_recent=payload.journal_recent,
            backtest_profile=payload.backtest_profile
        )

        ai_response = await ai_service.get_ai_decision(model_payload)

        # "choices" is returned by OpenAI – extract the JSON body
        try:
            raw = ai_response["choices"][0]["message"]["content"]
            decision_json = json.loads(raw)
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="AI returned an invalid JSON response."
            )

        return decision_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
