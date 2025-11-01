from fastapi import APIRouter, HTTPException
from services import mt5_service
from schemas import TradeRequest, TradeResponse, CloseTradeRequest, ModifyTradeRequest, CancelOrderRequest, TradePositionsResponse
from auth import get_current_user
from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(prefix="/trade", tags=["Trade Operations"])

@router.post("/open", response_model=TradeResponse)
def open_trade(req: TradeRequest):

    try:
        return mt5_service.open_trade(req.symbol, req.volume, req.order_type, req.sl, req.tp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------
# POST /trade/close
# -----------------------------
@router.post("/close", description="Close an existing open trade by ticket ID.")
def close_trade(request: CloseTradeRequest):
    result = mt5_service.close_trade(request.ticket)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# -----------------------------
# GET /trade/positions
# -----------------------------
@router.get("/positions", response_model=TradePositionsResponse, description="Get a list of all currently open trades/positions.")
def get_open_positions():
    positions = mt5_service.get_open_positions()
    if not positions:
        raise HTTPException(status_code=404, detail="No open positions found")
    return {"positions": positions, "total_positions": len(positions)}


# -----------------------------
# POST /trade/modify
# -----------------------------
@router.post("/modify", description="Modify SL/TP or volume of an open trade.")
def modify_trade(request: ModifyTradeRequest):
    result = mt5_service.modify_trade(request.ticket, request.stop_loss, request.take_profit, request.volume)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# -----------------------------
# POST /trade/cancel_order
# -----------------------------
@router.post("/cancel_order", description="Cancel a pending (not yet executed) order.")
def cancel_order(request: CancelOrderRequest):
    result = mt5_service.cancel_pending_order(request.order)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
