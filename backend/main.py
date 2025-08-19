import uvicorn
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.api.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# To run with uvicorn directly use: uvicorn app.api.main:app --reload