from fastapi import FastAPI, Depends
from routes import market, account, trade
import database
from contextlib import asynccontextmanager
from services import mt5_service
import auth
from routes import journal, instruments

# ---------- Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    database.Base.metadata.create_all(bind=database.engine)
    try:
        mt5_service.initialize()
        print("MT5 connected on startup")
    except Exception as e:
        print("Warning: MT5 failed to initialize", e)
    yield
    print("MT5 connection closed on shutdown")

app = FastAPI(
    title="FOREX Trading API",
    description="REST API for interacting with MetaTrader5 (MT5)",
    version="1.0.0",
    lifespan=lifespan
)

# Make the routes private (Token-protected routes)
app.include_router(market.router, dependencies=[Depends(auth.get_current_user)])
app.include_router(account.router, dependencies=[Depends(auth.get_current_user)])
app.include_router(trade.router, dependencies=[Depends(auth.get_current_user)])
app.include_router(instruments.router, dependencies=[Depends(auth.get_current_user)])
app.include_router(journal.router, dependencies=[Depends(auth.get_current_user)])

# Make the routes public
#app.include_router(market.router)
#app.include_router(account.router)
#app.include_router(trade.router)

@app.get("/")
def root():
    return {"message": "Welcome to the FOREX Trading API"}
