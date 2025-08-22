from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Explicitly register PostgreSQL dialect
try:
    import psycopg2
    # This should register the postgresql dialect
    from sqlalchemy.dialects import postgresql
    print("PostgreSQL dialect registered successfully")
except ImportError as e:
    print(f"Failed to import psycopg2: {e}")

# Determine if we're in production (Vercel) or using Supabase
is_production = os.environ.get("VERCEL_ENV") == "production"
use_supabase = os.environ.get("USE_SUPABASE", "false").lower() == "true"

# Don't create engine during import - create it lazily
def get_engine():
    if is_production or use_supabase:
        # Production: Use PostgreSQL with connection pooling
        # Ensure the URL uses the correct format
        db_url = settings.DATABASE_URL
        
        # Handle both postgres:// and postgresql:// formats
        if db_url.startswith("postgres://"):
            # Convert postgres:// to postgresql:// for SQLAlchemy
            db_url = db_url.replace("postgres://", "postgresql://")
        elif db_url.startswith("postgresql://"):
            # Already in correct format
            pass
        else:
            # Unknown format, try to use as-is
            pass
        
        # Add explicit psycopg2 dialect if not already present
        if "postgresql://" in db_url and "postgresql+psycopg2://" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
        
        print(f"Using database URL: {db_url[:50]}...")  # Log first 50 chars for debugging
        
        return create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20
        )
    else:
        # Development: Use SQLite (ignore DATABASE_URL if it's PostgreSQL)
        if settings.DATABASE_URL.startswith(("postgresql://", "postgres://")):
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