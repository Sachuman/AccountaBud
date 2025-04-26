import os
import json
import base64
import asyncio
from contextlib import asynccontextmanager

import ngrok
import pendulum
import pymongo
from twilio.rest import Client
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
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

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener = await ngrok.forward(8000, authtoken_from_env=True)
    app.state.ngrok_url = listener.url()
    app.state.twilio_client = Client(
        ACCOUNT_SID,
        AUTH_TOKEN,
    )
    scheduler.start()
    yield
    listener.close()
    scheduler.shutdown()


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
                await bridge.terminate()
                break

    except WebSocketDisconnect:
        await bridge.terminate()

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


@app.post("/action/reminder")
async def create_reminder(date: str, time: str, description: str, phone: str):
    """
    Create a reminder and schedule it
    """

    reminder = {
        "date": date,
        "time": time,
        "description": description,
        "type": "reminder",
        "phone": phone,
        "created_at": pendulum.now().isoformat(),
    }

    result = action_collection.insert_one(reminder)
    reminder_id = str(result.inserted_id)

    # Schedule the reminder
    try:
        date_format = "%Y-%m-%d %H:%M"
        scheduled_time = pendulum.strptime(f"{date} {time}", date_format)

        job_id = f"reminder_{reminder_id}"

        scheduler.add_job(
            make_reminder_call,
            "date",
            run_date=scheduled_time,
            args=[phone, reminder_id, description],
            id=job_id,
            replace_existing=True,
        )

        return {
            "success": True,
            "message": f"Reminder created and scheduled for {date} {time}",
            "id": reminder_id,
            "scheduled_time": scheduled_time.isoformat(),
        }
    except ValueError:
        return {
            "success": False,
            "message": f"Invalid date or time format: {date} {time}. Use YYYY-MM-DD and HH:MM formats.",
            "id": reminder_id,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error scheduling reminder: {str(e)}",
            "id": reminder_id,
        }


def make_reminder_call(phone, reminder_id, description):
    """
    Make a call for a scheduled reminder
    """
    try:
        print(f"Executing scheduled call for reminder {reminder_id}")

        # Custom message based on the description
        message = f"This is a reminder about: {description}"

        # Generate TwiML
        twiml = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>{message}</Say>
            <Pause length="1"/>
            <Say>This is an automated reminder. Thank you!</Say>
        </Response>
        """

        # We need to create a temporary endpoint for this TwiML
        # For now, we'll use the existing /twiml endpoint
        twiml_endpoint = f"{app.state.ngrok.url()}/twiml"
        status = 200

        try:
            app.state.twilio_client.calls.create(
                url=twiml_endpoint,
                to=phone,
                from_=TWILIO_PHONE_NUMBER,
            )
        except Exception:
            status = 500

        # Update the reminder in the database if needed
        # For example, mark it as completed or record the call status
        action_collection.update_one(
            {"_id": pymongo.ObjectId(reminder_id)},
            {
                "$set": {
                    "last_called": pendulum.now().isoformat(),
                    "call_status": status,
                }
            },
        )

    except Exception as e:
        print(f"Error making reminder call: {e}")
