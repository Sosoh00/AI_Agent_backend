from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import TradeJournalCreate, TradeJournalRead
from services import db_service

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post("/", response_model=TradeJournalRead)
def create_trade_journal_entry(data: TradeJournalCreate, db: Session = Depends(get_db)):
    return db_service.create_trade_journal(db, data)


@router.get("/recent", response_model=list[TradeJournalRead])
def get_recent(limit: int = 50, db: Session = Depends(get_db)):
    return db_service.get_recent_trades(db, limit)
