from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session, relationship
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, text
from typing import Annotated, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
import sys, os

# Add the parent directory to sys.path for local development
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    print(f"Added {parent_dir} to sys.path")

# Fix imports for different environments
try:
    # Try relative imports first (when running from backend directory)
    from ..db.database import Base, engine, SessionLocal
    from ..models.models import User
    from ..core import auth
    from ..core.auth import get_current_user
    print("Using relative imports")
except ImportError:
    try:
        # Try absolute imports with backend prefix (for Vercel)
        from backend.app.db.database import Base, engine, SessionLocal
        from backend.app.models.models import User
        from backend.app.core import auth
        from backend.app.core.auth import get_current_user
        print("Using backend.app.* imports")
    except ImportError:
        # Fallback to local imports (assuming we're in the app directory structure)
        from app.db.database import Base, engine, SessionLocal
        from app.models.models import User
        from app.core import auth
        from app.core.auth import get_current_user
        print("Using app.* imports")

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import traceback

# Global flag to avoid multiple table creation attempts
tables_created = False

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://*.vercel.app"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
try:
    app.include_router(auth.router)
except Exception as e:
    print(f"Error including router: {str(e)}")

# Create database tables on startup, but only once
if not tables_created:
    try:
        Base.metadata.create_all(bind=engine)
        tables_created = True
        print("Database tables created successfully")
        
        # Log which environment we're in
        env = os.environ.get("VERCEL_ENV", "development")
        print(f"Tables created in {env} environment")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        # In production, this might be expected if tables already exist

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/api/user", status_code=status.HTTP_200_OK)
async def user(user: user_dependency,  db : db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return {"User": user}


# For Vercel serverless function
@app.get("/api/health-check")
async def health_check():
    return {"status": "ok", "message": "FastAPI backend is running!"}


# Simple health check for troubleshooting
@app.get("/api/health")
async def basic_health():
    return {"status": "ok"}


# Initialize database tables in production (protected by special key)
@app.post("/api/init-db")
async def init_database(init_key: str):
    # Simple protection to prevent unauthorized table creation
    expected_key = os.environ.get("INIT_DB_KEY", "development-init-key")
    
    if init_key != expected_key:
        return {"status": "error", "message": "Invalid initialization key"}
    
    try:
        # Check if tables already exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Check what tables were created
        new_tables = inspector.get_table_names()
        created_tables = [t for t in new_tables if t not in existing_tables]
        
        return {
            "status": "success",
            "message": "Database initialization completed",
            "existing_tables": existing_tables,
            "created_tables": created_tables,
            "all_tables": new_tables
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


# Detailed environment check
@app.get("/api/debug")
async def debug_info():
    try:
        # Get environment info
        env_info = {
            "VERCEL_ENV": os.environ.get("VERCEL_ENV"),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "DATABASE_URL": os.environ.get("DATABASE_URL", "Not set").replace(
                os.environ.get("PGPASSWORD", ""), "[REDACTED]"
            ) if os.environ.get("DATABASE_URL") else "Not set",
            "sys.path": sys.path,
            "current_directory": os.getcwd(),
            "directory_contents": os.listdir(".")
        }
        
        # Test database connection without exposing credentials
        db_status = "Not tested"
        try:
            db = SessionLocal()
            # Use text() for raw SQL queries with SQLAlchemy 2.0+
            result = db.execute(text("SELECT 1")).scalar()
            db.close()
            db_status = f"Connected successfully (test query result: {result})"
        except Exception as e:
            db_status = f"Connection failed: {str(e)}"
            
        return {
            "status": "ok",
            "environment": env_info,
            "database": db_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


# Database connection test
@app.get("/api/db-test")
async def test_db_connection():
    try:
        # Test creating a session
        db = SessionLocal()
        # Run a simple query with text() for SQLAlchemy 2.0+ compatibility
        result = db.execute(text("SELECT 1")).scalar()
        db.close()
        return {"status": "ok", "connected": True, "test_query": result}
    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}


# Check database schema status
@app.get("/api/db-status")
async def check_db_status():
    try:
        from sqlalchemy import inspect, text
        
        # Test connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        
        # Check tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Check if users table exists and get column info
        users_table_info = None
        if 'users' in tables:
            users_columns = inspector.get_columns('users')
            users_table_info = {
                "exists": True,
                "columns": [col['name'] for col in users_columns]
            }
        else:
            users_table_info = {"exists": False}
        
        # Check if there are any users in the database
        user_count = 0
        if 'users' in tables:
            try:
                result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
                user_count = result
            except:
                user_count = "Unable to count"
        
        db.close()
        
        return {
            "status": "ok",
            "database_connected": True,
            "all_tables": tables,
            "users_table": users_table_info,
            "user_count": user_count,
            "environment": os.environ.get("VERCEL_ENV", "development")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


## running the app using uvicorn : uvicorn main:app --reload
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 