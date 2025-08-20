# api/main.py - Simplest possible test
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/test")
async def test():
    return {"status": "ok"} 