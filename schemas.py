from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Literal

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

class HistoricalDataResponse(BaseModel):
    
    symbol: str
    timeframe: str 
    historical_data: List[Candle] = Field(
        ..., example=[
            {
                "time": "2025-10-28T12:40:00+02:00",
                "open": 1.16609,
                "high": 1.16626,
                "low": 1.16598,
                "close": 1.16598,
                "tick_volume": 164
            },
            {
                "time": "2025-10-28T12:35:00+02:00",
                "open": 1.16602,
                "high": 1.16612,
                "low": 1.16595,
                "close": 1.16610,
                "tick_volume": 165
            }
        ]
    )


class MarketQuoteResponse(BaseModel):
    symbol: str
    bid: float
    ask: float
    last: float
    time: str

class TradeRequest(BaseModel):
    """
    Represents a trade order request.
    - symbol: The instrument to trade (e.g., 'EURUSD', 'XAUUSD').
    - volume: Lot size of the trade (e.g., 0.1 = micro lot, 1.0 = standard lot).
    - order_type: Type of trade — 'buy' or 'sell'.
    - sl: Stop Loss price level (optional).
    - tp: Take Profit price level (optional).
    """

    symbol: str = Field(..., example="EURUSD", description="Trading symbol, e.g., EURUSD, XAUUSD")
    volume: float = Field(..., gt=0, example=0.1, description="Trade volume (lot size), must be greater than 0")

    # restrict order_type to allowed values
    order_type: str = Field(
        ...,
        example="buy, sell, buylimit, selllimit, buystop, sellstop",
        description="Type of order. Options: 'buy', 'sell', 'buylimit', 'selllimit', 'buystop', 'sellstop'"
    )

    sl: Optional[float] = Field(
        None,
        example=1.08450,
        description="Stop Loss price level (optional). Example: for EURUSD, 1.08450"
    )

    tp: Optional[float] = Field(
        None,
        example=1.09450,
        description="Take Profit price level (optional). Example: for EURUSD, 1.09450"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EURUSD",
                "volume": 0.1,
                "order_type": "buy",
                "sl": 1.08450,
                "tp": 1.09450
            }
        }


class TradeResponse(BaseModel):
    order_id: int
    price: float
    volume: float
    type: str

# -------------------- TRADE SCHEMAS --------------------

class CloseTradeRequest(BaseModel):
    ticket: int = Field(..., example=1234567, description="MT5 trade ticket ID to close")

class ModifyTradeRequest(BaseModel):
    ticket: int = Field(..., example=1234567, description="Trade ticket ID to modify")
    stop_loss: Optional[float] = Field(None, example=1.0950, description="New Stop Loss price")
    take_profit: Optional[float] = Field(None, example=1.1050, description="New Take Profit price")
    volume: Optional[float] = Field(None, example=0.1, description="New volume in lots")

class CancelOrderRequest(BaseModel):
    order: int = Field(..., example=654321, description="Pending order ID to cancel")

class TradePosition(BaseModel):
    ticket: int
    symbol: str
    volume: float
    open_price: float
    stop_loss: float
    take_profit: float
    profit: float
    type: str
    time: str

class TradePositionsResponse(BaseModel):
    positions: List[TradePosition]
    total_positions: int

class AccountInformationResponse(BaseModel):
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    leverage: int
    currency: str
