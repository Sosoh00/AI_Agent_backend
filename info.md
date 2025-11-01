
Account Management Endpoints
    
    GET /account/info :Get general account info (login, name, broker, leverage).
        {
          "login": 1234567,
          "name": "Trader001",
          "broker": "ICMarkets",
          "leverage": 500
        }

    GET /account/balance :Get account financial status (balance, equity, margin, free margin, margin level).
        {
          "balance": 10250.75,
          "equity": 10480.50,
          "margin": 120.00,
          "free_margin": 10360.50,
          "margin_level": 8735.4
        }

    GET /account/history : Get historical trades or orders within a date range.
        {
           "ticket": 123456,
           "symbol": "EURUSD",
           "type": "buy",
           "volume": 0.5,
           "open_price": 1.0850,
           "close_price": 1.0910,
           "profit": 300.50,
           "open_time": "2025-10-25T09:30:00Z",
           "close_time": "2025-10-25T13:45:00Z"
         }

    GET /market/symbols :Get current market quote for a specific symbol.
      {
        "symbol": "EURUSD",
        "spread": 12,
        "digits": 5,
        "trade_mode": "full"
      }    

Market Data Endpoints

    GET /market/symbols :List all available trading symbols and their details (spread, digits, etc.)
    {
        "symbol": "EURUSD",
        "spread": 12,
        "digits": 5,
        "trade_mode": "full"
    }

    GET /market/quote/{symbol} :Get current market quote for a specific symbol.
    {
        "symbol": "EURUSD",
        "bid": 1.08495,
        "ask": 1.08505,
        "time": "2025-10-28T11:45:00Z"
    }

    GET /market/history/{symbol} :Fetch historical data (OHLC candles) for a symbol.

        { "time": "2025-10-28T11:00:00Z", "open": 1.0845, "high": 1.0850, "low": 1.0838, "close": 1.0849 },
        { "time": "2025-10-28T11:05:00Z", "open": 1.0849, "high": 1.0854, "low": 1.0846, "close": 1.0850 }
    
Trade Management Endpoints

    POST /trade/open :Open a trade/postion.

    body: 
    {
      "symbol": "EURUSD",
      "type": "buy",
      "volume": 0.1,
      "tp": 1.0900,
      "sl": 1.0800
    }
    response:{
      "status": "success",
      "ticket": 789456,
      "price": 1.08495
    }

    POST /trade/close :Close an open trade/position.
    body: {
      "ticket": 789456
    }
    response: 
    { "status": "closed", "profit": 25.60 }

    GET /trade/positions :Get a list of all currently open trades.
    response: 
    {
     "ticket": 789456,
     "symbol": "EURUSD",
     "type": "buy",
     "volume": 0.1,
     "open_price": 1.0849,
     "current_price": 1.0852,
     "profit": 3.00
    }

    GET /trade/pending_orders :Get all pending limit/stop orders.   
    {
      "ticket": 654321,
      "symbol": "GBPUSD",
      "type": "buy_limit",
      "price": 1.2650,
      "volume": 0.2
    }

    POST /trade/cancel_order
    body: 
    {
      "ticket": 654321
    }

    POST /trade/modify :Modify SL/TP or volume of an open trade.
    body: 
    {
      "ticket": 789456,
      "tp": 1.0910,
      "sl": 1.0830
    }