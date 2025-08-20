# api/main.py - Test environment variables
import os
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