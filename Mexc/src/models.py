from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20))
    order_id = Column(String(50))
    side = Column(String(10))
    price = Column(Float)
    amount = Column(Float)
    total = Column(Float)
    pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20))
    order_id = Column(String(50))
    side = Column(String(10))
    entry_price = Column(Float)
    amount = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    opened_at = Column(DateTime, default=datetime.utcnow)

class DailyStats(Base):
    __tablename__ = "daily_stats"
    id = Column(Integer, primary_key=True)
    date = Column(String(10), unique=True)
    initial_balance = Column(Float)
    current_balance = Column(Float)
    total_pnl = Column(Float, default=0.0)
    trades_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)