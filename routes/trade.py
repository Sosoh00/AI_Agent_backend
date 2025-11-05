from fastapi import APIRouter, HTTPException
from services import mt5_service
from schemas import BulkCloseFilter, BulkCloseResponse, PendingOrderCreateRequest, PendingOrderModifyRequest,PendingOrderResponse, PendingOrdersResponse, TradeRequest, TradeResponse, CloseTradeRequest, ModifyTradeRequest, CancelOrderRequest, TradePositionsResponse
from auth import get_current_user
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

router = APIRouter(prefix="/trade", tags=["Trade Operations"])


@router.post("/bulk-operations", response_model=BulkCloseResponse)
def bulk_close_orders(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTCUSDm)"),
    type: str = Query("all", description="buy, sell, pending, or all"),
    status: str = Query("open", description="open, pending, or all"),
    profit: str = Query("all", description="positive, negative, or all"),
    filter_body: Optional[BulkCloseFilter] = None
    ):
    """
        Bulk close multiple trades or pending orders in a single operation.
        You can filter by:
        - symbol
        - order type
        - profit/loss
        - status (open/pending)
    """

    # Merge query parameters and body (body overrides query)
    filter_data = {
        "symbol": filter_body.symbol if filter_body and filter_body.symbol else symbol,
        "type": filter_body.type if filter_body and filter_body.type else type,
        "status": filter_body.status if filter_body and filter_body.status else status,
        "profit": filter_body.profit if filter_body and filter_body.profit else profit
    }

    result = mt5_service.bulk_close_orders(filter_data)
    return result

@router.post("/open", response_model=TradeResponse)
def open_trade(request: TradeRequest):
    """
        Open a new trade (buy/sell) for a specific symbol with given volume, SL, TP.
    """
    symbol = request.symbol.upper()
    try:
        if not mt5_service.symbol_exists(symbol):
            symbol = symbol + "m"  # try with .m suffix
            if not mt5_service.symbol_exists(symbol):
                raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found on MT5")

        return mt5_service.open_trade(symbol, request.volume, request.order_type, request.sl, request.tp)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------
# POST /trade/close
# -----------------------------
@router.post("/close", description="Close an existing open trade by ticket ID.")
def close_trade(request: CloseTradeRequest):
    result = mt5_service.close_trade(request.ticket)
    #print(f'result: {result}')
    if isinstance(result, ValueError):
        raise HTTPException(status_code=404, detail=str(result))
    return {
        "status": "closed with success",
        "data": result
    }

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
# GET /trade/pending_orders
# -----------------------------
@router.get("/pending", response_model=PendingOrdersResponse, summary="Get all pending orders")
def get_pending_orders():
    result = mt5_service.get_pending_orders()

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "total_pending_orders": result["total_pending_orders"],
        "orders": result["orders"]
    }

# -----------------------------
# POST /trade/modify
# -----------------------------
@router.post("/active/modification", description="Modify SL/TP or volume/lot size of an open trade.")
def modify_trade(request: ModifyTradeRequest):
    result = mt5_service.modify_trade(request.ticket, request.stop_loss, request.take_profit, request.volume)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.post("/pending/modification", description="Modify pending order parameters.")
def modify_pending_order(request: PendingOrderModifyRequest):
    result = mt5_service.modify_pending_order(ticket=request.ticket, price=request.price, sl=request.sl, tp=request.tp, volume=request.volume)
    print(f'result: {result}')

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# -----------------------------
# POST /trade/pending-order
# -----------------------------
@router.post("/pending", response_model=PendingOrderResponse, description="Place a pending order (buy_limit/sell_limit/buy_stop/sell_stop)")
def create_pending_order(request: PendingOrderCreateRequest):
    symbol = request.symbol.upper()
    try:
        if not mt5_service.symbol_exists(symbol):
            symbol = symbol + "m"  # try with .m suffix
            if not mt5_service.symbol_exists(symbol):
                print(f"Symbol '{symbol}' not found on MT5")
                raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found on MT5")

        result = mt5_service.place_pending_order(symbol, order_type_str=request.order_type, price=request.price, volume=request.volume, sl=request.sl, tp=request.tp)
        print(f'result: {result}')
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# -----------------------------
# POST /trade/cancel-order
# -----------------------------
@router.post("/pending/cancel", description="Cancel a pending (not yet executed) order.")
def cancel_pending_order(request: CancelOrderRequest):
    result = mt5_service.cancel_pending_order(request.ticket)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
