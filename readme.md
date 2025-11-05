startting the ngrok tunnel:

1. ngrok config add-authtoken <your-token-here>
2. ngrok http 8000

starting the fastapi server:
run: uvicorn main:app --reload

FOREX/
│
├── __pycache__/
│
├── .env
├── .gitignore
├── requirements.txt
│
├── main.py                 # Entry point — only includes app creation and router registration
│
├── auth.py                 # Handles token authentication and user verification
├── database.py             # Handles DB connection (SQLite)
├── users.db
│
├── models.py               # Database models (e.g., User, maybe Trades)
├── schemas.py              # Pydantic schemas for all responses and requests
│
├── routes/                 # NEW folder for all API routes
│   ├── __init__.py
│   ├── market.py           # Endpoints: /market/quote, /market/history
│   ├── account.py          # Endpoints: /account/balance , account/infos
│   ├── trade.py            # Endpoints: /trade/open, /trade/close, /trade/modify, /trade/cancel, /trade/positions
│
├── services/               # NEW folder for backend logic
│   ├── __init__.py
│   ├── mt5_service.py      # Handles MetaTrader5 operations (connect, fetch, trade, etc.)
│
├── info.md
├── readme.md
├── secrets.md
└── test.py

Order Type	                Value	Meaning
ORDER_TYPE_BUY	            0	    Market Buy
ORDER_TYPE_SELL	            1	    Market Sell
ORDER_TYPE_BUY_LIMIT	    2	    Pending Buy Limit
ORDER_TYPE_SELL_LIMIT	    3	    Pending Sell Limit
ORDER_TYPE_BUY_STOP	        4	    Pending Buy Stop
ORDER_TYPE_SELL_STOP	    5	    Pending Sell Stop
ORDER_TYPE_BUY_STOP_LIMIT	6	    Pending Buy Stop Limit
ORDER_TYPE_SELL_STOP_LIMIT	7	    Pending Sell Stop Limit
ORDER_TYPE_CLOSE_BY	        8	    Close By Order

# Catch known MT5 retcodes for clarity
retcodes = {
    10004: "Invalid volume",
    10006: "Trade context busy",
    10016: "Invalid stops",
    10030: "Invalid request",
    10031: "Invalid price",
    10032: "Invalid expiration",
}

ORDER_TYPE_BUY	            0	Market Buy
ORDER_TYPE_SELL	            1	Market Sell
ORDER_TYPE_BUY_LIMIT	    2	Buy Limit
ORDER_TYPE_SELL_LIMIT	    3	Sell Limit
ORDER_TYPE_BUY_STOP	        4	Buy Stop
ORDER_TYPE_SELL_STOP	    5	Sell Stop
ORDER_TYPE_BUY_STOP_LIMIT	6	Buy Stop Limit
ORDER_TYPE_SELL_STOP_LIMIT	7	Sell Stop Limit
ORDER_TYPE_CLOSE_BY	        8	Close By Order

