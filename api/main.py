# api/main.py
import sys, os
import traceback

# Make root available for module import
sys.path.append(os.getcwd())

try:
    from backend.app.api.main import app  # Your FastAPI app instance
    print("✅ Successfully imported FastAPI app from backend.app.api.main")
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
    
    # Re-raise the error with more context
    raise ImportError(f"Failed to import FastAPI app: {e}\nTraceback: {traceback.format_exc()}")

# Vercel will use `app` automatically—no `if __name__` needed. 