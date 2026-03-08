from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./api_logs.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class APILog(Base):
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    endpoint = Column(String, index=True)
    method = Column(String)
    response_time_ms = Column(Float)
    status_code = Column(Integer)
    payload_size = Column(Integer)
    ip_address = Column(String)
    user_id = Column(String, nullable=True)
    is_simulation = Column(Boolean, default=False, index=True)  # Separate live from simulation
    malicious_pattern = Column(String, nullable=True)  # Track SQL_INJECTION, XSS_ATTACK, etc.
    query_params = Column(String, nullable=True)  # Store query parameters for analysis
    request_count = Column(Integer, default=1)  # Track request volume for DDoS detection


class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    endpoint = Column(String)
    method = Column(String)
    risk_score = Column(Float)
    priority = Column(String)
    failure_probability = Column(Float)
    anomaly_score = Column(Float)
    is_anomaly = Column(Boolean)
    usage_cluster = Column(Integer)
    req_count = Column(Integer)
    error_rate = Column(Float)
    avg_response_time = Column(Float)
    max_response_time = Column(Float)
    payload_mean = Column(Float)
    unique_endpoints = Column(Integer)
    repeat_rate = Column(Float)
    status_entropy = Column(Float)
    anomaly_type = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)
    is_simulation = Column(Boolean, default=False, index=True)  # Separate live from simulation


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
