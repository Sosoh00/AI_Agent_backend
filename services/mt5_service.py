import MetaTrader5 as mt5
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv
from fastapi import HTTPException
import os

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
    return {"order_id": result.order, "price": price, "volume": volume, "type": order_type}



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

def close_trade(ticket: int):
    ensure_connection()
    position = mt5.positions_get(ticket=ticket)
    if not position:
        return {"success": False, "message": f"No open position found for ticket {ticket}"}
    pos = position[0]
    order_type = mt5.ORDER_SELL if pos.type == 0 else mt5.ORDER_BUY
    close_price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": order_type,
        "position": ticket,
        "price": close_price,
        "deviation": 10,
        "magic": 123456,
        "comment": "Closed via API",
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"success": False, "message": f"Close failed: {result.comment}"}
    return {"success": True, "message": f"Trade {ticket} closed successfully"}

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

def cancel_pending_order(order: int):
    ensure_connection()
    result = mt5.order_delete(order)
    if not result:
        return {"success": False, "message": f"Failed to cancel order {order}"}
    return {"success": True, "message": f"Order {order} cancelled successfully"}
