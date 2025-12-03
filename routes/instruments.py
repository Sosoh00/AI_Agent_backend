from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import InstrumentCreate, InstrumentRead
from services import db_service

router = APIRouter(prefix="/instruments", tags=["Instruments"])


@router.post("", response_model=InstrumentRead)
def create_instrument_route(data: InstrumentCreate, db: Session = Depends(get_db)):
    return db_service.create_instrument(db, data)


@router.get("/{symbol}", response_model=InstrumentRead)
def get_instrument_route(symbol: str, db: Session = Depends(get_db)):
    item = db_service.get_instrument(db, symbol)
    if not item:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return item


@router.get("", response_model=list[InstrumentRead])
def get_all_instruments_route(db: Session = Depends(get_db)):
    return db_service.get_instruments(db)
