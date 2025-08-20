# api/main.py
import sys, os
import traceback

# Make root available for module import
sys.path.append(os.getcwd())

# Create a minimal app for testing
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/test")
async def test_endpoint():
    return {"status": "ok", "message": "API is working"}

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

try:
    from backend.app.api.main import app as backend_app
    print("✅ Successfully imported FastAPI app from backend.app.api.main")
    
    # Include the backend routes
    app.mount("/api/auth", backend_app)
    
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"Directory contents: {os.listdir('.')}")
    
    # Try to see if backend directory exists
    if os.path.exists('backend'):
        print(f"Backend directory contents: {os.listdir('backend')}")
        if os.path.exists('backend/app'):
            print(f"Backend/app directory contents: {os.listdir('backend/app')}")
    
    # Create a fallback app with debug endpoint
    @app.get("/api/debug-import")
    async def debug_import():
        return {
            "error": str(e),
            "cwd": os.getcwd(),
            "python_path": sys.path,
            "directory_contents": os.listdir("."),
            "backend_exists": os.path.exists("backend"),
            "backend_contents": os.listdir("backend") if os.path.exists("backend") else []
        }
    
    print(f"Created fallback app with debug endpoint")

# Vercel will use `app` automatically—no `if __name__` needed. 