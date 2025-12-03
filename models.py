from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

from pydantic import BaseModel

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    tokens = relationship("Token", back_populates="owner")

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="tokens")


class TokenCreate(BaseModel):
    username: str
    name: str = "n8n_token"  # optional label for token


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    description = Column(String, nullable=True)
    session = Column(String, nullable=True)
    volatility_profile = Column(Text, nullable=True)
    backtest_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TradeJournal(Base):
    __tablename__ = "trade_journal"

    id = Column(Integer, primary_key=True, index=True)

    # Core trade info
    symbol = Column(String, index=True)
    direction = Column(String)            # buy / sell
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float, nullable=True)
    take_profit_2 = Column(Float, nullable=True)
    take_profit_3 = Column(Float, nullable=True)

    position_size = Column(Float)
    risk_pct = Column(Float)

    # Trade status + PnL
    status = Column(String, default="open")   # open/closed/cancelled
    result_pnl = Column(Float, nullable=True)

    # AI reasoning + memory snapshots
    confidence = Column(Float)
    reasoning = Column(Text)
    snapshot_json = Column(Text)        # LTF + HTF candle data at entry
    sentiment_json = Column(Text)       # News sentiment at entry

    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
