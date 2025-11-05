from unittest import result
import MetaTrader5 as mt5
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv
from fastapi import HTTPException
import os

from urllib3 import request

def initialize():
    load_dotenv()
    login = int(os.getenv("MT5_LOGIN"))
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER")
   
    #print(login, password, server)
    # Always ensure clean start
    mt5.shutdown()
    if not mt5.initialize(login=login, password=password, server=server):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    print(f"Connected to {server}")

def ensure_connection():
    """Ensure MT5 connection is active."""
    if not mt5.initialize():
        raise ConnectionError(f"MT5 initialization failed: {mt5.last_error()}")
    if not mt5.terminal_info():
        raise ConnectionError("MT5 terminal not responding or not logged in.")
    return True

def symbol_exists(symbol: str) -> bool:
    """Check if a symbol exists on the connected MT5 terminal."""
    ensure_connection()

    all_symbols = mt5.symbols_get()
    if all_symbols is None:
        raise RuntimeError("Failed to retrieve symbols list. MT5 not initialized or not connected.")
    return any(s.name == symbol for s in all_symbols)

def connect():
    if not mt5.initialize():
        raise RuntimeError(f"Failed to initialize MT5: {mt5.last_error()}")

def disconnect():
    mt5.shutdown()


def get_account_information():
    """
    Fetches account information (balance, equity, margin, etc.) from MT5.
    Returns a dictionary matching the AccountInfoResponse schema.
    """
    # Ensure MT5 connection is active
    if not mt5.initialize():
        raise HTTPException(status_code=500, detail="Failed to connect to MT5 terminal.")

    try:
        info = mt5.account_info()
        if info is None:
            raise HTTPException(status_code=500, detail="Unable to retrieve account information from MT5.")

        # Return data in the same structure as AccountInfoResponse
        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "margin_level": info.margin_level,
            "leverage": info.leverage,
            "currency": info.currency
        }
    finally:
        mt5.shutdown()

def get_historical_data(symbol: str, candlesticks: int, timeframe: str = "H1"):
    """Fetch historical candles safely from MT5 and adjust timestamps to local SAST (UTC+2)."""
    ensure_connection()

    if not mt5.symbol_select(symbol, True):
        raise ValueError(f"Failed to select symbol {symbol}. Error: {mt5.last_error()}")
    print(f'timeframe: {timeframe}, candles: {candlesticks}')
    timeframe_map = {
        "1MIN": mt5.TIMEFRAME_M1,
        "5MIN": mt5.TIMEFRAME_M5,
        "15MIN": mt5.TIMEFRAME_M15,
        "30MIN": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
    }

    tf = timeframe_map.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Invalid timeframe: {timeframe}")

    rates = mt5.copy_rates_from_pos(symbol, tf, 0, candlesticks)
    if rates is None:
        raise ValueError(f"No data returned for symbol {symbol}")

    # Broker info (optional diagnostic)
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info and symbol_info.time:
        server_time = symbol_info.time
        print(f"Broker server time for {symbol}: {datetime.fromtimestamp(server_time)}")
        #offset_hours = (server_datetime - utc_now.replace(tzinfo=None)).total_seconds() / 360
    # Convert to DataFrame
    df = pd.DataFrame(rates)

    # Convert timestamp to datetime and adjust to SAST (UTC+2)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)  # start as UTC
    #df["time"] = df["time"].dt.tz_convert("Africa/Johannesburg")  # convert to SAST

    return df[["time", "open", "high", "low", "close", "tick_volume"]]


def get_quote(symbol: str):
    """Fetch current market quote (bid, ask, etc.) for a symbol."""
    ensure_connection()

    quote = mt5.symbol_info_tick(symbol)
    if quote is None:
        raise ValueError(f"No tick data available for symbol '{symbol}'.")
    
    return {
        "symbol": symbol,
        "bid": quote.bid,
        "ask": quote.ask,
        "last": quote.last,
        "time": datetime.fromtimestamp(quote.time).isoformat()
    }

def open_trade(symbol: str, volume: float, order_type: str, sl: float = None, tp: float = None):
    connect()
    order_type_enum = mt5.ORDER_TYPE_BUY if order_type.lower() == "buy" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if order_type_enum == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_enum,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "API trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    disconnect()
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise RuntimeError(f"Trade failed: {result.comment}")
    return {"ticket": result.order, "price": price, "volume": volume, "type": order_type}


def get_open_positions():
    ensure_connection()
    positions = mt5.positions_get()
    if not positions:
        return []
    result = []
    for pos in positions:
        result.append({
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "open_price": pos.price_open,
            "stop_loss": pos.sl,
            "take_profit": pos.tp,
            "profit": pos.profit,
            "type": "BUY" if pos.type == 0 else "SELL",
            "time": datetime.fromtimestamp(pos.time).isoformat(),
        })
    return result

def get_pending_orders():
    ensure_connection()
    pending_orders = mt5.orders_get()

    if not pending_orders:
        return {"status": "error", "message": f"Failed to retrieve pending orders: {mt5.last_error()}"}

    if len(pending_orders) == 0:
        return {"status": "success", "orders": [], "total_pending_orders": 0}

    pending_order_map = {
            2: "Buy Limit",
            3: "Sell Limit",
            4: "Buy Stop",
            5: "Sell Stop",
            6: "Buy Stop Limit",
            7: "Sell Stop Limit",
            8: "Close By Order"
        }
    
    order_list = []
    for order in pending_orders:
        order_type = mt5.ORDER_TYPE_BUY_LIMIT if order.type == 2 else (mt5.ORDER_TYPE_SELL_LIMIT if order.type == 3 else order.type)
        order_list.append({
            "ticket": order.ticket,
            "symbol": order.symbol,
            "volume": order.volume_initial,
            "price_open": order.price_open,
            "order_type": pending_order_map[order_type] if order_type in pending_order_map else "Unknown",
            "sl": order.sl,
            "tp": order.tp,
            "time_setup": datetime.fromtimestamp(order.time_setup)
        })
        
    return {"status": "success", "orders": order_list, "total_pending_orders": len(order_list)}


def close_trade(ticket: int):
    """
    Close an open trade by its ticket ID.
    """

    ensure_connection()

    position = mt5.positions_get(ticket=ticket)
    if not position:
        return ValueError(f"No open position found for ticket {ticket}")

    pos = position[0]

    # Determine opposite order type for closing
    if pos.type == mt5.POSITION_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
    elif pos.type == mt5.POSITION_TYPE_SELL:
        order_type = mt5.ORDER_TYPE_BUY
    else:
        raise ValueError("Unknown position type")

    # Get latest price
    symbol = pos.symbol
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        raise ValueError(f"Failed to get tick data for {symbol}")

    close_price = tick.bid if order_type == mt5.ORDER_TYPE_BUY else tick.ask

    # Make sure the symbol is selected
    if not mt5.symbol_select(symbol, True):
        raise ValueError(f"Symbol {symbol} not available")

    # Construct request (short comment)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": pos.volume,
        "type": order_type,
        "position": ticket,
        "price": close_price,
        "deviation": 20,
        "magic": 123456,
        "comment": "API close",  # keep it short and ASCII only
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if result is None:
        raise ValueError(f"Trade close failed: {mt5.last_error()}")

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise ValueError(f"Failed to close trade: {result.comment} ({result.retcode})")

    return {
        "ticket": ticket,
        "symbol": symbol,
        "closed_price": close_price,
        "volume": pos.volume,
        "profit": pos.profit,
        "time_closed": datetime.now().isoformat(),
        "message": "success"
    }



def modify_trade(ticket: int, sl=None, tp=None, volume=None):
    ensure_connection()
    position = mt5.positions_get(ticket=ticket)
    if not position:
        return {"success": False, "message": f"No position found for ticket {ticket}"}
    pos = position[0]

    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": pos.symbol,
        "position": ticket,
        "sl": sl if sl else pos.sl,
        "tp": tp if tp else pos.tp,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"success": False, "message": f"Modification failed: {result.comment}"}
    return {"success": True, "message": f"Trade {ticket} modified successfully"}

def cancel_pending_order(ticket: int):
    ensure_connection()
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": ticket,
        "comment": "cancel_pending",
    }
    result = mt5.order_send(request)
    print(f'result: {result}'  )
    if not result:
        return {"success": False, "message": f"Failed to cancel order {ticket}"}
    return {"success": True, "message": f"Order {ticket} cancelled successfully"}

# services/mt5_service.py (append)

def _pending_order_type_from_str(s: str):
    """Map string to MT5 pending order type constants."""
    s = s.lower()
    mapping = {
        "buy_limit": mt5.ORDER_TYPE_BUY_LIMIT,
        "sell_limit": mt5.ORDER_TYPE_SELL_LIMIT,
        "buy_stop": mt5.ORDER_TYPE_BUY_STOP,
        "sell_stop": mt5.ORDER_TYPE_SELL_STOP,
    }
    return mapping.get(s)

def place_pending_order(symbol: str, order_type_str: str, price: float, volume: float, sl=None, tp=None):
    """
    Place a pending order (limit or stop).
    Returns dict: {"success": True, "message": "Pending order placed", "order": result._asdict()} on success or {"success": False, "message": "Error message"} on error.
    """
    ensure_connection()

    if not mt5.symbol_select(symbol, True):
        return {"success": False, "message": f"Symbol {symbol} not available or not selectable"}

    pending_type = _pending_order_type_from_str(order_type_str)
    if pending_type is None:
        return {"success": False, "message": f"Invalid order_type '{order_type_str}'. Use: buy_limit, sell_limit, buy_stop, sell_stop"}

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": float(volume),
        "type": pending_type,
        "price": float(price),
        "sl": float(sl) if sl is not None else 0.0,
        "tp": float(tp) if tp is not None else 0.0,
        "deviation": 20,
        "magic": 123456,
        "comment": "pending_api",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }

    result = mt5.order_send(request)
    if result is None:
        return {"success": False, "message": f"Order send failed: {mt5.last_error()}"}

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        order = {
            "ticket": result.order,
            "symbol": symbol,
            "type": order_type_str,
            "price": request["price"],
            "volume": request["volume"],
            "sl": request["sl"],
            "tp": request["tp"],
            "comment": request["comment"],
        }
        return {"success": True, "message": "Pending order placed", "order": order}

    return {
        "success": False,
        "message": f"Failed to place pending order (retcode={result.retcode})",
        "error_info": mt5.last_error()
    }

def modify_pending_order(ticket: int, price: float = None, sl: float = None, tp: float = None, volume: float = None):
    """
    Modify an existing pending order (price, SL, TP, volume).
    Returns dict result with status/message/order.
    """
    
    
    # Ensure connection is alive
    if not ensure_connection():
        return {"success": False, "message": "MetaTrader5 connection failed"}

    # Retrieve the specific pending order
    orders = mt5.orders_get(ticket=ticket)
    if orders is None:
        return {"success": False, "message": f"MT5 API error: {mt5.last_error()}"}

    if not orders:
        return {"success": False, "message": f"No pending order found for ticket {ticket}"}

    order = orders[0]

    # Ensure it’s not a market order
    if order.type in (0, 1):  # BUY/SELL
        return {"success": False, "message": f"Order {ticket} is a market order, not pending"}

    # Normalize zero SL/TP to None
    sl = None if sl == 0 else sl
    tp = None if tp == 0 else tp

    # Validate stop levels if both are present
    if sl is not None and tp is not None and sl >= tp:
        return {"success": False, "message": "Invalid stops: SL must be less than TP"}

    # Build the modification request
    request = {
        "action": mt5.TRADE_ACTION_MODIFY,
        "order": ticket,
        "symbol": order.symbol,
        "price": float(price) if price is not None else order.price_open,
        "comment": "modified_api",
    }

    # Only include SL/TP if they’re non-None
    if sl is not None:
        request["sl"] = float(sl)
    if tp is not None:
        request["tp"] = float(tp)
    if volume:
        request["volume"] = float(volume)

    # Send the modification request
    result = mt5.order_send(request)

    if not result:
        return {"success": False, "message": f"Modify request failed: {mt5.last_error()}"}

    if hasattr(result, "retcode"):
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            order = {
                "ticket": result.order,
                "symbol": order.symbol,
                "type": order.type,
                "price": request["price"],
                "volume": request["volume"],
                "sl": sl if sl is not None else order.sl,
                "tp": tp if tp is not None else order.tp,
                "comment": request["comment"],
        }
            return {
                "success": True,
                "message": f"Pending order {ticket} modified successfully",
                "order": order,
            }

        retcodes = {
            10004: "Invalid volume",
            10006: "Trade context busy",
            10016: "Invalid stops",
            10030: "Invalid request",
            10031: "Invalid price",
            10032: "Invalid expiration",
        }

        readable_error = retcodes.get(result.retcode, "Unknown error")
        return {
            "success": False,
            "message": f"Modify failed ({result.retcode}): {readable_error}",
            "order": result._asdict(),
        }

    return {
        "success": False,
        "message": f"Unexpected result: {result}",
    }


def make_trade_result(trade, trade_category: str, success: bool, message: str) -> dict:
    """
    Helper to construct a consistent result dictionary for each closed trade.
    """
    return {
        "ticket": trade.ticket,
        "symbol": trade.symbol,
        "type": trade_category,  # must match schema field name
        "success": success,
        "message": message
    }


def bulk_close_orders(filter_criteria: dict):
    """
    Close multiple positions or pending orders based on filter criteria.
    
    Filter options:
        symbol: str (e.g., "EURUSD")
        type: str ("buy", "sell", "pending", "all")
        status: str ("open", "pending", "all")
        profit: str ("positive", "negative", "all")
    """
    ensure_connection()

    # --- Extract filter criteria ---
    symbol_filter = filter_criteria.get("symbol", "")
    trade_type_filter = filter_criteria.get("type", "all").lower()        # buy, sell, pending, all
    trade_status_filter = filter_criteria.get("status", "open").lower()   # open, pending, all
    profit_filter = filter_criteria.get("profit", "all").lower()          # positive, negative, all

    # --- Validate symbol ---
    try:
        if not symbol_exists(symbol_filter):
            # Try appending 'm' for brokers like GBPUSDm
            symbol_filter_with_m = symbol_filter + "m"
            if symbol_exists(symbol_filter_with_m):
                symbol_filter = symbol_filter_with_m
            else:
                raise HTTPException(status_code=404, detail=f"Symbol '{symbol_filter}' not found on MT5")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    print(f"Applying filters -> symbol: {symbol_filter}, type: {trade_type_filter}, status: {trade_status_filter}, profit: {profit_filter}")

    # --- Retrieve trades ---
    open_positions = mt5.positions_get() or []
    pending_orders = mt5.orders_get() or []

    # --- Determine target trades based on status filter ---
    target_trades = []
    if trade_status_filter in ("open", "all"):
        for position in open_positions:
            target_trades.append(("position", position))
    if trade_status_filter in ("pending", "all"):
        for order in pending_orders:
            target_trades.append(("pending", order))

    results = []
    closed_count = 0

    # --- Process each trade ---
    for trade_category, trade in target_trades:
        print(f"\nProcessing ticket: {trade.ticket}, symbol: {trade.symbol}, category: {trade_category}")

        # --- Symbol filter ---
        if symbol_filter and trade.symbol != symbol_filter:
            continue

        # --- Trade type filter ---
        if trade_type_filter != "all":
            if trade_category == "position":
                is_buy_position = trade.type == mt5.ORDER_TYPE_BUY
                is_sell_position = trade.type == mt5.ORDER_TYPE_SELL

                if trade_type_filter == "buy" and not is_buy_position:
                    continue
                if trade_type_filter == "sell" and not is_sell_position:
                    continue
            elif trade_category == "pending":
                is_buy_order = trade.type in (mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP)
                is_sell_order = trade.type in (mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP)

                if trade_type_filter == "buy" and not is_buy_order:
                    continue
                if trade_type_filter == "sell" and not is_sell_order:
                    continue
                if trade_type_filter == "pending" and trade_category != "pending":
                    continue

        # --- Profit filter (only for positions) ---
        if profit_filter != "all" and trade_category == "position":
            if profit_filter == "positive" and trade.profit <= 0:
                continue
            if profit_filter == "negative" and trade.profit >= 0:
                continue

        # --- Execute close/remove action ---
        if trade_category == "position":
            result = close_trade(trade.ticket)
        else:  # pending orders
            remove_request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": trade.ticket,
                "symbol": trade.symbol
            }
            result = mt5.order_send(remove_request)

        # --- Handle result ---
        print('\n\nresult_retcode:',(result.keys()))
        print('\n\nresults:', result.values()  )
        if result and result['message'] == 'success' and mt5.TRADE_RETCODE_DONE == result.get("retcode", mt5.TRADE_RETCODE_DONE):
            closed_count += 1
            results.append(make_trade_result(trade, trade_category, True, "Trade closed successfully"))
        else:
            results.append(make_trade_result(
                trade, trade_category, False,
                f"Failed to close trade: {getattr(result, 'retcode', mt5.last_error())}"
        ))

    return {
        "success": closed_count > 0,
        "message": f"{closed_count}/{len(results)} trades closed successfully",
        "results": results
    }
