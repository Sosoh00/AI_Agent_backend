from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sqlite3

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./instruments.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def get_connection():
    conn = sqlite3.connect("instruments.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        direction TEXT,
        entry_price REAL,
        stop_loss REAL,
        take_profit_1 REAL,
        take_profit_2 REAL,
        take_profit_3 REAL,
        position_size REAL,
        risk_pct REAL,
        status TEXT,
        result_pnl REAL,
        confidence REAL,
        reasoning TEXT,
        snapshot_json TEXT,
        sentiment_json TEXT,
        opened_at TEXT,
        closed_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        description TEXT,
        session TEXT,
        volatility_profile TEXT,
        backtest_json TEXT,
        created_at TEXT
    );
    """)

    conn.commit()
    conn.close()

init_db()
