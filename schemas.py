from pydantic import BaseModel
from datetime import datetime
from typing import List

class TokenCreate(BaseModel):
    name: str
    username: str

class TokenOut(BaseModel):
    token: str
    name: str
    username: str
    created_at: datetime


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"


class Candle(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int

class SymbolDataResponse(BaseModel):
    Timezone: str
    symbol: str
    timeframe: str
    candles: int
    historical_data: List[Candle]