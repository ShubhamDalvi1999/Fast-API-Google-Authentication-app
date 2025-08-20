# api/main.py - Complete FastAPI application with Google OAuth
import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Annotated

# Import the complete backend application
try:
    from backend.app.api.main import app as backend_app
    from backend.app.db.database import get_db, get_engine
    from backend.app.core.auth import get_current_user
    from backend.app.models.models import User
    from backend.app.core.config import settings
    print("✅ Successfully imported backend application")
except Exception as e:
    print(f"❌ Failed to import backend: {e}")
    # Create a minimal app if import fails
    backend_app = FastAPI()

# Create the main app
app = FastAPI(title="FastAPI Google OAuth App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "https://*.vercel.app",
        "https://fast-api-google-authentication-app.vercel.app",
        "https://fast-api-google-authentication-bqox186fi.vercel.app",
        "https://fast-api-google-authentication-kwvqzt2cd.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes from the backend app
app.mount("/api", backend_app)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "FastAPI Google OAuth Application", "status": "running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Application is running"}

# Test database connection
@app.get("/test-db")
async def test_database():
    try:
        from backend.app.db.database import get_engine
        from sqlalchemy import text
        
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {"database": "✅ Connected", "result": result.scalar()}
    except Exception as e:
        return {"database": f"❌ Error: {str(e)}"}

# Test Google OAuth configuration
@app.get("/test-oauth")
async def test_oauth():
    try:
        from backend.app.core.config import settings
        return {
            "google_client_id": "✅ SET" if settings.GOOGLE_CLIENT_ID else "❌ NOT SET",
            "google_client_secret": "✅ SET" if settings.GOOGLE_CLIENT_SECRET else "❌ NOT SET",
            "google_redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        return {"oauth": f"❌ Error: {str(e)}"}

# Initialize database tables
@app.post("/init-db")
async def init_database():
    try:
        from backend.app.db.database import get_engine, Base
        from sqlalchemy import text
        
        engine = get_engine()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Test the connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
        
        return {
            "status": "✅ SUCCESS",
            "message": "Database tables created successfully",
            "user_count": user_count
        }
    except Exception as e:
        return {
            "status": "❌ FAILED",
            "error": str(e),
            "error_type": type(e).__name__
        }

# Keep the test endpoints for debugging
@app.get("/api/test")
async def test():
    return {"status": "ok"}

@app.get("/api/env-test")
async def env_test():
    return {
        "VERCEL_ENV": os.environ.get("VERCEL_ENV"),
        "GOOGLE_CLIENT_ID": "SET" if os.environ.get("GOOGLE_CLIENT_ID") else "NOT SET",
        "GOOGLE_CLIENT_SECRET": "SET" if os.environ.get("GOOGLE_CLIENT_SECRET") else "NOT SET",
        "GOOGLE_REDIRECT_URI": "SET" if os.environ.get("GOOGLE_REDIRECT_URI") else "NOT SET",
        "SECRET_KEY": "SET" if os.environ.get("SECRET_KEY") else "NOT SET",
        "DATABASE_URL_UNPOOLED": "SET" if os.environ.get("DATABASE_URL_UNPOOLED") else "NOT SET"
    }

@app.get("/api/import-test")
async def import_test():
    results = {}
    
    # Test basic imports
    try:
        from backend.app.core.config import settings
        results["config"] = "✅ SUCCESS"
    except Exception as e:
        results["config"] = f"❌ FAILED: {str(e)}"
    
    try:
        # Test importing database modules without initializing engine
        from backend.app.db.database import Base, get_engine, get_session_local, get_db
        results["database_import"] = "✅ SUCCESS"
    except Exception as e:
        results["database_import"] = f"❌ FAILED: {str(e)}"
    
    try:
        from backend.app.models.models import User
        results["models"] = "✅ SUCCESS"
    except Exception as e:
        results["models"] = f"❌ FAILED: {str(e)}"
    
    try:
        from backend.app.core.auth import router
        results["auth"] = "✅ SUCCESS"
    except Exception as e:
        results["auth"] = f"❌ FAILED: {str(e)}"
    
    return results

@app.get("/api/db-test")
async def db_test():
    """Test database connection without importing during startup"""
    try:
        from backend.app.db.database import get_engine
        from backend.app.core.config import settings
        from sqlalchemy import text
        
        # Log the original database URL (without credentials)
        original_url = settings.DATABASE_URL
        if original_url.startswith(("postgresql://", "postgres://")):
            # Mask credentials in the URL
            parts = original_url.split("@")
            if len(parts) > 1:
                masked_original = f"{parts[0].split('://')[0]}://***:***@{parts[1]}"
            else:
                masked_original = f"{original_url.split('://')[0]}://***:***@***"
        else:
            masked_original = original_url
            
        # Test SQLAlchemy dialect registration
        try:
            from sqlalchemy.dialects import registry
            dialects = registry.impls
            postgres_dialects = [d for d in dialects.keys() if 'postgres' in d.lower()]
        except Exception as e:
            postgres_dialects = f"Error checking dialects: {str(e)}"
        
        # Test psycopg2 import
        try:
            import psycopg2
            psycopg2_version = psycopg2.__version__
        except Exception as e:
            psycopg2_version = f"Import failed: {str(e)}"
        
        # Test engine creation
        engine = get_engine()
        
        # Get the actual URL used by the engine
        engine_url = str(engine.url)
        if engine_url.startswith(("postgresql://", "postgres://")):
            parts = engine_url.split("@")
            if len(parts) > 1:
                masked_engine_url = f"{parts[0].split('://')[0]}://***:***@{parts[1]}"
            else:
                masked_engine_url = f"{engine_url.split('://')[0]}://***:***@***"
        else:
            masked_engine_url = engine_url
        
        # Test connection with SQLAlchemy 2.0 compatible syntax
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            test_result = result.scalar()
            return {
                "database": "✅ SUCCESS - Connected",
                "test_query_result": test_result,
                "original_url": masked_original,
                "engine_url": masked_engine_url,
                "psycopg2_version": psycopg2_version,
                "postgres_dialects": postgres_dialects,
                "engine_type": str(type(engine))
            }
    except Exception as e:
        return {
            "database": f"❌ FAILED: {str(e)}",
            "error_type": type(e).__name__,
            "original_url": getattr(settings, 'DATABASE_URL', 'Not available')[:50] + "..." if len(getattr(settings, 'DATABASE_URL', '')) > 50 else getattr(settings, 'DATABASE_URL', 'Not available')
        } 