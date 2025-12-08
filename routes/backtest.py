from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services import db_service
import auth
from datetime import datetime
from typing import Dict, Any, Optional

router = APIRouter(prefix="/backtest", tags=["Backtest"])


class BacktestUploadRequest(BaseModel):
    symbol: str
    backtest_json: Dict[str, Any]
    description: Optional[str] = None
    session: Optional[str] = None
    volatility_profile: Optional[str] = None


class BacktestUploadResponse(BaseModel):
    success: bool
    instrument_id: int
    message: Optional[str] = None


@router.post("/upload", response_model=BacktestUploadResponse)
def upload_backtest(payload: BacktestUploadRequest, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    """
    Save or update backtest data tied to an instrument.
    This writes into your `instruments` table (backtest_json column).
    If instrument exists, update backtest_json; else create instrument.
    """
    try:
        existing = db_service.get_instrument(db, payload.symbol)
        if existing:
            # update fields
            existing.backtest_json = json.dumps(payload.backtest_json)
            if payload.description:
                existing.description = payload.description
            if payload.session:
                existing.session = payload.session
            if payload.volatility_profile:
                existing.volatility_profile = payload.volatility_profile
            db.commit()
            db.refresh(existing)
            return {"success": True, "instrument_id": existing.id, "message": "updated"}
        else:
            # create instrument via db_service.create_instrument
            create_payload = {
                "symbol": payload.symbol,
                "description": payload.description or "",
                "session": payload.session or "",
                "volatility_profile": payload.volatility_profile or "",
                "backtest_json": json.dumps(payload.backtest_json)
            }
            item = db_service.create_instrument(db, create_payload)
            return {"success": True, "instrument_id": item.id, "message": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
