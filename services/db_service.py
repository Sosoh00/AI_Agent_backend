from sqlalchemy.orm import Session
from models import Instrument, TradeJournal
from schemas import InstrumentCreate, TradeJournalCreate
from datetime import datetime


# --------------------------- Instruments CRUD ---------------------------

def create_instrument(db: Session, data: InstrumentCreate):
    item = Instrument(**data.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_instrument(db: Session, symbol: str):
    return db.query(Instrument).filter(Instrument.symbol == symbol).first()


def get_instruments(db: Session):
    return db.query(Instrument).all()


# --------------------------- Trade Journal CRUD ---------------------------

def create_trade_journal(db: Session, data: TradeJournalCreate):
    item = TradeJournal(**data.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_trade(db: Session, trade_id: int):
    return db.query(TradeJournal).filter(TradeJournal.id == trade_id).first()


def get_recent_trades(db: Session, limit: int = 50):
    return (
        db.query(TradeJournal)
        .order_by(TradeJournal.id.desc())
        .limit(limit)
        .all()
    )


def close_trade(db: Session, trade_id: int, result_pnl: float):
    item = db.query(TradeJournal).filter(TradeJournal.id == trade_id).first()
    if item:
        item.status = "closed"
        item.result_pnl = result_pnl
        item.closed_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
    return item
