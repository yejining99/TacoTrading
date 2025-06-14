from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base
import datetime

class TrumpStatement(Base):
    __tablename__ = "trump_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, unique=True, index=True)
    korean_translation = Column(Text, nullable=True)
    source = Column(String(255))
    posted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # AI 분석 결과
    keywords = Column(String(500), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    trade_relevance = Column(Float, nullable=True)
    taco_probability = Column(Float, nullable=True)
    
    is_analyzed = Column(Boolean, default=False)

class TACOSignal(Base):
    __tablename__ = "taco_signals"
    
    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, nullable=False)
    signal_type = Column(String(10))  # BUY, SELL, WATCH
    confidence = Column(Float)
    
    affected_etfs = Column(JSON)
    entry_timing = Column(String(20), default="immediate")
    expected_duration = Column(Integer, default=24)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class ETFPrice(Base):
    __tablename__ = "etf_prices"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    description = Column(String(100), nullable=True)
    price = Column(Float, nullable=False)
    change_percent = Column(Float, default=0.0)
    volume = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())