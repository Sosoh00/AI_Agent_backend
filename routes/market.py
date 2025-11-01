from fastapi import APIRouter, Query, HTTPException
from services import mt5_service
from schemas import MarketQuoteResponse,HistoricalDataResponse
import json
from fastapi import Depends
from auth import get_current_user
import auth

from services import mt5_service

router = APIRouter(prefix="/market", tags=["Market"])

@router.get("/quote/{symbol}", response_model=MarketQuoteResponse)
def get_quote(symbol: str):
    """
        Get current market quote for a specific symbol.
        Returns bid, ask, last price, and timestamp.
    """
    symbol = symbol.upper()
    try:# Check if symbol exists on MT5
        if not mt5_service.symbol_exists(symbol):
            symbol = symbol + "m"  # try with .m suffix
            if not mt5_service.symbol_exists(symbol):
                raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found on MT5")

        data = mt5_service.get_quote(symbol)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.get("/quotes/{symbol}/history", response_model=HistoricalDataResponse)
def get_historical_data(
    symbol: str,
    timeframe: str = Query(
        "H1",
        enum=["1min", "5min", "15min", "30min", "h1", "h4", "d1", "w1", "mn1"]
    ),
    candlesticks: int = Query(5, ge=1, le=1000, description="Number of candles to fetch"),
   
):
    try:
        # Normalize inputs
        symbol = symbol.upper()
        tf_normalized = timeframe.upper()
        if tf_normalized in ["1MIN", "5MIN", "15MIN", "30MIN"]:
            pass  # already valid
        elif tf_normalized in ["H1", "H4", "D1", "W1", "MN1"]:
            pass
        else:
            raise HTTPException(status_code=400, detail=f"Invalid timeframe '{timeframe}'")

        # Validate candlesticks explicitly (redundant but extra safety)
        if not isinstance(candlesticks, int) or not (1 <= candlesticks <= 1000):
            raise HTTPException(
                status_code=400,
                detail="Candlesticks must be an integer between 1 and 1000"
            )
        # Check if symbol exists on MT5
        if not mt5_service.symbol_exists(symbol):
            symbol = symbol + "m"  # try with .m suffix
            if not mt5_service.symbol_exists(symbol):
                raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found on MT5")

        # Fetch data safely
        df = mt5_service.get_historical_data(symbol, candlesticks, tf_normalized)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data returned from MT5")
        
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Reverse order: newest candles first
    df = df.iloc[::-1].reset_index(drop=True)
    return {
    
        "symbol": symbol,
        "timeframe": tf_normalized,
        "historical_data": df.to_dict(orient="records")
    }