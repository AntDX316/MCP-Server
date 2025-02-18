from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta
import os

# Create the database engine
DATABASE_URL = "sqlite:///./mcp_server.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ConnectionRecord(Base):
    __tablename__ = "connection_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    connections = Column(Integer, nullable=False)

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_connection_record(connections: int, timestamp: datetime = None):
    """Add a new connection record to the database"""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    db = SessionLocal()
    try:
        record = ConnectionRecord(timestamp=timestamp, connections=connections)
        db.add(record)
        db.commit()
    finally:
        db.close()

def get_connection_history(hours: int = 1):
    """Get connection history for the last n hours"""
    db = SessionLocal()
    try:
        # Calculate the timestamp for n hours ago
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get records after the cutoff
        records = db.query(ConnectionRecord)\
            .filter(ConnectionRecord.timestamp >= cutoff)\
            .order_by(ConnectionRecord.timestamp.asc())\
            .all()
        
        # Ensure UTC timezone is explicitly set in the response
        return [{
            "timestamp": record.timestamp.replace(tzinfo=timezone.utc).isoformat(),
            "connections": record.connections
        } for record in records]
    finally:
        db.close()

def cleanup_old_records(hours: int = 1):
    """Delete records older than n hours"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        db.query(ConnectionRecord)\
            .filter(ConnectionRecord.timestamp < cutoff)\
            .delete()
        db.commit()
    finally:
        db.close() 