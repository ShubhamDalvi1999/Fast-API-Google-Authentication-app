from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings
import os

# Determine if we're in production (Vercel)
is_production = os.environ.get("VERCEL_ENV") == "production"

# Don't create engine during import - create it lazily
def get_engine():
    if is_production:
        # Production: Use PostgreSQL with connection pooling
        return create_engine(
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
            return create_engine(
                "sqlite:///./database.db",
                connect_args={"check_same_thread": False}
            )
        else:
            # Use the configured DATABASE_URL (should be SQLite)
            return create_engine(
                settings.DATABASE_URL,
                connect_args={"check_same_thread": False}
            )

# Create session factory
def get_session_local():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()