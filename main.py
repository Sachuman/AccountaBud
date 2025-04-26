"""
Main FastAPI application for LA Hacks 2025 project.
Handles Twilio calls, reminders, and websocket communication.
"""

import os
import json
from contextlib import asynccontextmanager

# Third-party imports
import ngrok
import pendulum
import pymongo
from twilio.rest import Client
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient

# Local imports
from call.call import start_call

# ============================================================================
# Configuration and Setup
# ============================================================================

load_dotenv()

# Environment variables
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
MONGO_URL = os.getenv("MONGO_URL")

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client.get_database("La-Hacks")
action_collection = db.get_collection("action_restrictions")

# Scheduler for reminders
scheduler = BackgroundScheduler()


# ============================================================================
# FastAPI Application Setup
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Set up and tear down application resources."""
    # Setup
    listener = await ngrok.forward(8000, authtoken_from_env=True)
    app.state.ngrok_url = listener.url()
    app.state.twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)
    scheduler.start()

    yield

    # Teardown
    listener.close()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


# ============================================================================
# Models
# ============================================================================


class BrowserUsage(BaseModel):
    """Browser usage tracking model."""

    date: str
    email: str
    domain: str
    active_time: int


class CallRequest(BaseModel):
    """Request model for making calls."""

    phone: str


# ============================================================================
# Helper Functions
# ============================================================================


def create_twilio_call(phone: str, twiml_endpoint: str):
    """Create a Twilio call to the specified phone number."""
    try:
        call = app.state.twilio_client.calls.create(
            url=twiml_endpoint,
            to=phone,
            from_=TWILIO_PHONE_NUMBER,
        )
        return {"success": True, "sid": call.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}


def make_reminder_call(phone: str, reminder_id: str, description: str):
    """Make a call for a scheduled reminder."""
    try:
        print(f"Executing scheduled call for reminder {reminder_id}")
        twiml_endpoint = f"{app.state.ngrok_url}/twiml"

        call_result = create_twilio_call(phone, twiml_endpoint)
        status = 200 if call_result["success"] else 500

        # Update the reminder status in the database
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


# ============================================================================
# Basic Routes
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint providing basic app status."""
    print("Ngrok URL:", app.state.ngrok_url)
    return {"message": "Hello, World!", "status": "running"}


@app.post("/usage")
async def usage(usage_data: BrowserUsage):
    """Track browser usage data."""
    print(f"Received usage data: {usage_data}")
    return {"message": "Usage data received!"}


# ============================================================================
# Call Handling Routes
# ============================================================================


@app.post("/call")
def call(request: CallRequest):
    """Initiate a call to the specified phone number."""
    phone = request.phone
    print(f"Calling {phone}...")
    twiml_endpoint = f"{app.state.ngrok_url}/twiml"

    result = create_twilio_call(phone, twiml_endpoint)
    if result["success"]:
        return {"message": "Call initiated!", "sid": result["sid"]}
    else:
        return {"message": "Failed to initiate call", "error": result["error"]}, 500


@app.post("/twiml", response_class=Response)
async def twiml(request: Request):
    """Return TwiML XML to Twilio for Media Streams setup."""
    wss_url = app.state.ngrok_url.replace("https", "wss")
    return templates.TemplateResponse(
        request=request,
        name="streams.xml",
        context={"url": wss_url},
    )


@app.websocket("/")
async def websocket_endpoint(ws: WebSocket):
    """Handle WebSocket connection for audio streaming."""
    await ws.accept()

    start_data = ws.iter_text()
    await start_data.__anext__()
    call_data = json.loads(await start_data.__anext__())
    print(call_data, flush=True)

    stream_sid = call_data["start"]["streamSid"]
    print("WebSocket connection accepted")

    await start_call(ws, stream_sid)


# ============================================================================
# Action and Restriction Routes
# ============================================================================


@app.get("/action/restriction/{website}")
async def check_restriction(website: str):
    """
    Check if a website is restricted and optionally call the associated phone number.

    Args:
        website: Website URL to check
        make_call: If True, will make a call to the phone number if restriction exists
    """
    print(f"Checking restriction for {website}")
    restriction = action_collection.find_one({"website": website})

    if not restriction:
        return {"restricted": False}

    print(f"Restriction found: {restriction}")

    if restriction.get("phone", None):
        twiml_endpoint = f"{app.state.ngrok_url}/twiml"
        call_result = create_twilio_call(restriction["phone"], twiml_endpoint)
        return {"restricted": True, "call_initiated": call_result["success"]}

    return {"restricted": True, "call_initiated": False}


@app.post("/action/reminder")
async def create_reminder(date: str, time: str, description: str, phone: str):
    """
    Create a reminder and schedule it.

    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format
        description: Reminder description
        phone: Phone number to call
    """
    # Create reminder document
    reminder = {
        "date": date,
        "time": time,
        "description": description,
        "type": "reminder",
        "phone": phone,
        "created_at": pendulum.now().isoformat(),
    }

    # Store in database
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
