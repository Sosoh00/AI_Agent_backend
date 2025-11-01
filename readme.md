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
