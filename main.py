
from contextlib import asynccontextmanager
import auth
import mt5_data_api
import database
import database
from fastapi import FastAPI, Query
from fastapi import APIRouter
from fastapi import FastAPI, HTTPException
from schemas import SymbolDataResponse

from fastapi import Depends
from auth import get_current_user


router = APIRouter()

# ---------- Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    database.Base.metadata.create_all(bind=database.engine)
    try:
        mt5_data_api.initialize()
        print("MT5 connected on startup")
    except Exception as e:
        print("Warning: MT5 failed to initialize", e)
    yield
    mt5_data_api.shutdown_connection()
    print("MT5 connection closed on shutdown")

# ---------- FastAPI app ----------
app = FastAPI(title="MT5 Historical Data API", lifespan=lifespan)

# Mount auth router
app.include_router(auth.router)

@app.get("/v1")
def home():
    return {"status": "ok"}

# ---------- Data endpoint ----------

VALID_TIMEFRAMES = ["1MIN", "5MIN", "15MIN", "30MIN", "H1", "H4", "D1", "W1", "MN1"]

@app.get("/v1/assets/{symbol}", response_model=SymbolDataResponse)
def get_symbol_data(
    symbol: str,
    timeframe: str = Query(
        "H1",
        enum=["1min", "5min", "15min", "30min", "h1", "h4", "d1", "w1", "mn1"]
    ),
    candlesticks: int = Query(5, ge=1, le=1000, description="Number of candles to fetch"),
    #current_user=Depends(get_current_user)
    
    current_user=Depends(auth.get_current_user)  # enforce token check
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
        if not mt5_data_api.symbol_exists(symbol):
            symbol = symbol + "m"  # try with .m suffix
            if not mt5_data_api.symbol_exists(symbol):
                raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found on MT5")

        # Fetch data safely
        df = mt5_data_api.get_historical_data(symbol, candlesticks, tf_normalized)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data returned from MT5")
        
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Reverse order: newest candles first
    df = df.iloc[::-1].reset_index(drop=True)
    return {
        "Timezone": "SAST",
        "symbol": symbol,
        "timeframe": tf_normalized,
        "candles": len(df),
        "historical_data": df.to_dict(orient="records")
    }
