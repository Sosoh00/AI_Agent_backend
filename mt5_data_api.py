# mt5_data_api.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
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
    """Ensure MT5 is connected; reconnect if not."""
    if not mt5.initialize():
        print("MT5 not connected. Reconnecting...")
        initialize()

def symbol_exists(symbol: str) -> bool:
    """Check if a symbol exists in MT5."""
    all_symbols = mt5.symbols_get()
    return any(s.name.upper() == symbol.upper() for s in all_symbols)

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
