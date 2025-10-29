import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# --- Replace with your credentials ---
#LOGIN = 211843170
#PASSWORD = "Mrmtnt@11_5.."  # strongly suggest using environment variables
#SERVER = "Exness-MT5Trial9"


LOGIN = 390889149
PASSWORD = "Mrmtnt@11_5.."  # strongly suggest using environment variables
SERVER = "XMGlobal-MT5 14"

# Initialize connection
if not mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER):
    print("initialize() failed, error code =", mt5.last_error())
else:
    print("Connected to MT5 account:", LOGIN)

symbol = "EURUSD"
timeframe = mt5.TIMEFRAME_H1
rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1000)

# Convert to Pandas DataFrame for convenience
data = pd.DataFrame(rates)
data['time'] = pd.to_datetime(data['time'], unit='s')
print(data)
#print("Rates returned:", rates)
symbols = mt5.symbols_get()
print(type(symbols))
#count = 0
#for symbol in symbols:
#    if 'USD' in symbol.name and 'm' in symbol.name:
#        print(f"{symbol.name}")
#        count += 1
#print("Total count:", count)

#from sqlalchemy.orm import Session
#import database, models
#
#db: Session = database.SessionLocal()
#t = db.query(models.Token).all()
#for token in t:
#    print(token.token, token.owner.username)
