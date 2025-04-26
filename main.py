from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class BrowserUsage(BaseModel):
    date: str
    email: str
    domain: str
    active_time: int


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.post("/usage")
async def usage(usage: BrowserUsage):
    print(f"Received usage data: {usage}")
    return {"message": "Usage data received!"}


@app.post("/call")
async def call():
    return {"message": "Call request received!"}
