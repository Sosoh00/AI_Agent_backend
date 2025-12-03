from pydantic import BaseModel, ConfigDict, Field
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
    ticket: int
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
    volume: Optional[float] = Field(None, example=0.02, description="New volume/lot size is optional, the field can be empty")

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

#Pending orders schemas
class PendingOrder(BaseModel):
    ticket: int
    symbol: str
    volume: float
    price_open: float
    order_type: str
    sl: float
    tp: float
    time_setup: datetime
#Pending orders response schema
class PendingOrdersResponse(BaseModel):
    total_pending_orders: int
    orders: list[PendingOrder]
#Create pending order response schema
class PendingOrderResponse(BaseModel):
    success: bool
    message: str
    order: Optional[dict] = None

class CancelOrderRequest(BaseModel):
    ticket: int = Field(..., example=654321, description="Pending order ID to cancel")

class PendingOrderCreateRequest(BaseModel):
    symbol: str = Field(..., example="EURUSD", description="Symbol to place pending order on")
    order_type: str = Field(..., example="buy_limit",
                            description="One of: buy_limit, sell_limit, buy_stop, sell_stop")
    price: float = Field(..., example=1.08450, description="Price at which pending order should be triggered")
    volume: float = Field(..., gt=0, example=0.1, description="Volume in lots")
    sl: Optional[float] = Field(None, example=1.08000, description="Optional stop loss price")
    tp: Optional[float] = Field(None, example=1.09000, description="Optional take profit price")
    #expiration: Optional[datetime] = Field(None, description="Optional expiration datetime (ISO) for the pending order")

class PendingOrderModifyRequest(BaseModel):
    ticket: int = Field(..., example=1877501123, description="Pending order ticket to modify")
    price: Optional[float] = Field(None, example=1.08500, description="New pending order price")
    sl: Optional[float] = Field(None, example=1.08000, description="New stop loss price")
    tp: Optional[float] = Field(None, example=1.09000, description="New take profit price")
    volume: Optional[float] = Field(None, gt=0, example=0.2, description="New volume in lots")

# -------------------- Bulk Operations Schemas --------------------



#class BulkCloseFilter(BaseModel):
#    symbols: Optional[List[str]] = None
#    type: Optional[Literal["buy", "sell", "pending", "all"]] = Field("all")
#    status: Optional[Literal["open", "pending", "all"]] = Field("open")
#    profit: Optional[Literal["positive", "negative", "all"]] = Field("all")


class BulkCloseFilter(BaseModel):
    """
    Filters to select which trades or pending orders to close.
    All fields are optional and can be combined.
    """

    symbol: Optional[str] = Field(None, description="Filter by symbol (e.g., BTCUSDm)")
    type: str = Field("all", description="buy, sell, pending, or all")
    status: str = Field("open", description="open, pending, or all")
    profit: str = Field("all", description="positive, negative, or all")
    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTCUSDm",
                "type": "buy",
                "status": "open",
                "profit": "positive",
            }
        }

class BulkCloseResult(BaseModel):
    """
    Result for each individual trade or order closed in the bulk operation.
    """
    ticket: int = Field(..., description="Ticket (order ID) of the trade or pending order.")
    symbol: str = Field(..., description="Trading symbol of the closed trade/order.")
    type: str = Field(..., description="Order type: BUY, SELL, PENDING, etc.")
    success: bool = Field(..., description="Whether this order was successfully closed.")
    message: str = Field(..., description="Detailed result or MT5 return code.")


class BulkCloseResponse(BaseModel):
    """
    Aggregated response for bulk close operation.
    """
    success: bool = Field(..., description="True if at least one trade/order closed successfully.")
    message: str = Field(..., description="Summary of the bulk close operation.")
    results: List[BulkCloseResult] = Field(..., description="List of individual close results.")

# ----------------------------
# Instrument Schemas
# ----------------------------

class InstrumentBase(BaseModel):
    symbol: str
    description: Optional[str] = None
    session: Optional[str] = None
    volatility_profile: Optional[str] = None
    backtest_json: Optional[str] = None


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentRead(InstrumentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ----------------------------
# Trade Journal Schemas
# ----------------------------

class TradeJournalBase(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    position_size: float
    risk_pct: float
    confidence: float
    reasoning: str
    snapshot_json: str
    sentiment_json: str
    status: str = "open"


class TradeJournalCreate(TradeJournalBase):
    pass


class TradeJournalRead(TradeJournalBase):
    id: int
    result_pnl: Optional[float] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
