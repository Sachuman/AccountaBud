import os
import json
import base64
import asyncio
from contextlib import asynccontextmanager

import ngrok
from twilio.rest import Client
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient

from call.bridge import GeminiAudioBridge

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
MONGO_URL = os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)
db = client.get_database("La-Hacks")
action_collection = db.get_collection("action_restrictions")


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener = await ngrok.forward(8000, authtoken_from_env=True)
    app.state.ngrok_url = listener.url()
    app.state.twilio_client = Client(
        ACCOUNT_SID,
        AUTH_TOKEN,
    )
    yield
    listener.close()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    print("Ngrok URL:", app.state.ngrok_url)
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


class CallRequest(BaseModel):
    phone: str


@app.post("/call")
def call(request: CallRequest):
    phone = request.phone
    print(f"Calling {phone}...")
    twiml_endpoint = f"{app.state.ngrok_url}/twiml"
    call = app.state.twilio_client.calls.create(
        url=twiml_endpoint, to=phone, from_=TWILIO_PHONE_NUMBER
    )
    return {"message": "Call initiated!", "sid": call.sid}


@app.post("/twiml", response_class=Response)
async def twiml(request: Request):
    """
    Return TwiML XML to Twilio for Media Streams setup.
    """
    wss_url = app.state.ngrok_url.replace("https", "wss")
    return templates.TemplateResponse(
        request=request,
        name="streams.xml",
        context={"url": wss_url},
    )


@app.websocket("/")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    bridge = GeminiAudioBridge()
    stream_sid = None

    async def send_audio_chunk(chunk: bytes):
        if not stream_sid:
            return

        await ws.send_json(
            {
                "event": "media",
                "media": {
                    "payload": base64.b64encode(chunk).decode(),
                    "track": "outbound",
                },
                "streamSid": stream_sid,
            }
        )

    gemini_task = asyncio.create_task(bridge.start(send_audio_chunk))

    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            event = data.get("event")

            if event == "start":
                stream_sid = data["streamSid"]
                continue
            if event == "media" and data["media"].get("track") == "inbound":
                pcm = base64.b64decode(data["media"]["payload"])
                await bridge.add_request(pcm)
                continue
            if event == "stop":
                bridge.terminate()
                break

    except WebSocketDisconnect:
        bridge.terminate()

    finally:
        await gemini_task
        await ws.close()


@app.get("/action/restriction/{website}")
async def check_restriction(website: str, make_call: bool = True):
    """
    Check if a website is restricted and optionally make a call to the associated phone number

    Args:
        website: Website URL to check
        make_call: If True, will make a call to the phone number if restriction exists
    """

    print(f"Checking restriction for {website}")
    restriction = action_collection.find_one({"website": website})
    print(f"Restriction found: {restriction}")

    if restriction and make_call and "phone" in restriction and restriction["phone"]:
        twiml_endpoint = f"{app.state.ngrok_url}/twiml"
        app.state.twilio_client.calls.create(
            url=twiml_endpoint,
            to=restriction["phone"],
            from_=TWILIO_PHONE_NUMBER,
        )
