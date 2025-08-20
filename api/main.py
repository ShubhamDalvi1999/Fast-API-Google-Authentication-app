# api/main.py - Test backend imports without DB initialization
import os
import sys
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

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
        from backend.app.db.database import Base, get_engine, get_session_local
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
        engine = get_engine()
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return {"database": "✅ SUCCESS - Connected"}
    except Exception as e:
        return {"database": f"❌ FAILED: {str(e)}"} 