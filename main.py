import os
from contextlib import asynccontextmanager

import requests
import ngrok
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global NGROK_PUBLIC_URL
    listener = await ngrok.forward(8080, authtoken_from_env=True)
    app.state.ngrok = listener
    yield
    listener.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


class BrowserUsage(BaseModel):
    date: str
    email: str
    domain: str
    active_time: int


@app.post("/usage")
async def usage(usage: BrowserUsage):
    print(f"Received usage data: {usage}")
    return {"message": "Usage data received!"}


@app.post("/call")
def call(phone: str):
    twiml_endpoint = f"{app.state.ngrok.url()}/twiml"
    payload = {
        "Url": twiml_endpoint,
        "To": phone,
        "From": TWILIO_PHONE_NUMBER,
    }
    resp = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Calls.json",
        data=payload,
        auth=(ACCOUNT_SID, AUTH_TOKEN),
    )
    print(f"Status: {resp.status_code}\n{resp.text}")
    return {"message": "Call initiated!"}


@app.websocket("/")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_bytes()
        # TODO: Process the call data
