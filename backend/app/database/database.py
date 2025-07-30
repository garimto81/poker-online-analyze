from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Use SQLite as fallback for testing
if not os.getenv("DATABASE_URL"):
    print("[WARNING] DATABASE_URL not set, using SQLite for testing")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Add connect_args for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
