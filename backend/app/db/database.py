from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys

# Debug information
print(f"Loading database.py module")
print(f"VERCEL_ENV: {os.environ.get('VERCEL_ENV')}")
print(f"DATABASE_URL exists: {bool(os.environ.get('DATABASE_URL'))}")

# Check if we're in development or production mode
IS_PRODUCTION = os.environ.get("VERCEL_ENV") == "production"

if IS_PRODUCTION:
    # Use Neon PostgreSQL in production
    DATABASE_URL = os.environ.get("DATABASE_URL")
    print(f"Using production database connection")
    
    if not DATABASE_URL:
        print("WARNING: DATABASE_URL not set in production environment!")
        # Fallback to SQLite if DATABASE_URL is not set
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
        DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
        print(f"Falling back to SQLite: {DATABASE_URL}")
    
    # For SQLAlchemy 1.4+ compatibility
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        print(f"Converted postgres:// to postgresql:// for SQLAlchemy compatibility")
    
    try:
        # Create engine for PostgreSQL with reduced connection pooling for serverless
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Helps with connection issues after idle time
            pool_recycle=300,    # Recycle connections every 5 minutes
            pool_size=5,         # Reduced from 20 to minimize connections
            max_overflow=10,     # Maximum number of connections that can be created beyond pool_size
            connect_args={"connect_timeout": 15}  # Add connection timeout
        )
        print(f"Created PostgreSQL engine successfully")
    except Exception as e:
        print(f"Error creating database engine: {str(e)}")
        # Fallback to SQLite in case of connection error
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
        DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        print(f"Falling back to SQLite: {DATABASE_URL}")
else:
    # Use SQLite in development
    print(f"Using development database connection (SQLite)")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
    print(f"SQLite path: {DATABASE_PATH}")
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # Create engine for SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print(f"Created SQLite engine successfully")

# Create a session for the database which is used to interact with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for the database, this is used to create the tables in the database
Base = declarative_base()

print(f"Database setup complete")