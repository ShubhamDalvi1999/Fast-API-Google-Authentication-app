from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings
import os

# Determine if we're in production (Vercel)
is_production = os.environ.get("VERCEL_ENV") == "production"

if is_production:
    # Production: Use PostgreSQL with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20
    )
else:
    # Development: Use SQLite (ignore DATABASE_URL if it's PostgreSQL)
    if settings.DATABASE_URL.startswith("postgresql://"):
        # Use SQLite for local development
        engine = create_engine(
            "sqlite:///./database.db",
            connect_args={"check_same_thread": False}
        )
    else:
        # Use the configured DATABASE_URL (should be SQLite)
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False}
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()