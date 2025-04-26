import os
import datetime
from contextlib import asynccontextmanager

import ngrok
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import google.generativeai as genai
from langchain_core.output_parsers import JsonOutputParser


load_dotenv()

# Environment variables
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
AGENT_ID_RESTRICTION = os.getenv("RETELL_AGENT_ID_RESTRICTION")
AGENT_ID_REMINDER = os.getenv("RETELL_AGENT_ID_REMINDER")
MONGO_URL = os.getenv("MONGO_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RETELL_PHONE_NUMBER = os.getenv("RETELL_PHONE_NUMBER")

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client.get_database("La-Hacks")
action_collection = db.get_collection("action_restrictions")
reminder_collection = db.get_collection("action_reminders")

# Initialize scheduler for reminders
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup ngrok
    listener = await ngrok.forward(8000, authtoken_from_env=True)
    app.state.ngrok_url = listener.url()

    # Setup RetellAI client
    app.state.retell_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RETELL_API_KEY}",
    }

    # Setup Gemini model
    genai.configure(api_key=GEMINI_API_KEY)
    app.state.gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    # Start scheduler
    scheduler.start()

    yield

    # Cleanup
    scheduler.shutdown()
    listener.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    print("Ngrok URL:", app.state.ngrok_url)
    return {"message": "Hello, World!"}


class BrowserUsage(BaseModel):
    date: str
    email: str
    domain: str
    active_time: int


class TranscriptRequest(BaseModel):
    transcript: str


@app.post("/process-transcript")
async def process_transcript_endpoint(data: TranscriptRequest):
    """
    Process transcript using Gemini and store in database
    """
    await process_transcript(data.transcript)


async def process_transcript(transcript: str):
    """
    Process transcript using Gemini to determine intent and structure
    """
    now = datetime.datetime.now().isoformat()
    prompt = f"""
Analyze the following transcript from a phone call and determine if it's for:
1. Setting a restriction on a website
2. Setting a reminder for a task

THERE ARE CAN BE MULTIPLE RESTRICTIONS AND REMINDERS IN THE TRANSCRIPT. PLEASE REVIEW AND RETURN ALL OF THEM.
UNDERSTAND what user wants, identify all reminders and it can have multiple times. identify all restrictions and it can have multiple domains.
we need json for each restriction and reminder. If there is a daily event, create multiple reminders for each day.

If it's a restriction, extract:
- domain (the website to restrict)
- description (reason for restriction)
- phone (the user's phone number if mentioned, otherwise set to empty string)

If it's a reminder, extract:
- date (in YYYY-MM-DD format, use today's date if not specified)
- time (in HH:MM format)
- description (what to remind about)
- phone (the user's phone number if mentioned, otherwise set to empty string)

RESPOND ONLY WITH A VALID JSON OBJECT. Do not include any explanations, markdown formatting, or code blocks.
The JSON must have a "type" field that is either "restriction" or "reminder", plus the other extracted fields.

HARCODE phone number to +18636676483 for now. Today's date is {now}.
Example response for a reminder:
{{"type": "reminder", "date": "2023-04-15", "time": "07:00", "description": "Wake up call", "phone": "+1234567890"}}

Example response for a restriction:
{{"type": "restriction", "domain": "facebook.com", "description": "Avoid social media", "phone": "+1234567890"}}

Transcript: {transcript}
"""

    try:
        response = app.state.gemini_model.generate_content(prompt)

        response_text = response.text

        parser = JsonOutputParser()

        result = parser.parse(response_text)

        # Add current date and timestamp
        result["created_at"] = now

        if result["type"] == "RESTRICTION":
            # Store restriction in database
            action_collection.insert_one(result)
            print(f"Stored new restriction: {result}")

        elif result["type"] == "reminder":
            # Store reminder in database
            reminder_id = reminder_collection.insert_one(result).inserted_id

            # Schedule reminder if time is specified
            if result.get("time") and result.get("phone"):
                schedule_reminder(
                    str(reminder_id),
                    result["date"],
                    result["time"],
                    result["phone"],
                    result["description"],
                )
                print(f"Scheduled reminder: {result}")

    except Exception as e:
        print(f"Error processing transcript: {e}")
        print(
            f"Response text: {response.text if 'response' in locals() else 'No response'}"
        )

    return str(result)


def schedule_reminder(
    reminder_id: str, date_str: str, time_str: str, phone: str, description: str
):
    """
    Schedule a reminder call
    """
    try:
        # Parse date and time
        reminder_datetime = datetime.datetime.strptime(
            f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
        )

        # Add job to scheduler
        scheduler.add_job(
            make_reminder_call,
            "date",
            run_date=reminder_datetime,
            args=[reminder_id, phone, description],
        )
    except Exception as e:
        print(f"Error scheduling reminder: {e}")


async def make_reminder_call(reminder_id: str, phone: str, description: str):
    """
    Make a call to remind the user
    """
    try:
        # Request body for RetellAI call API
        call_payload = {
            "to_number": phone,
            "from_number": RETELL_PHONE_NUMBER,
            "override_agent_id":AGENT_ID_REMINDER,
            "retell_llm_dynamic_variables": {
                "reminder_description": {description}
            }

        }

        # Make API call to RetellAI
        response = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers=app.state.retell_headers,
            json=call_payload,
        )

        # The response is successful if we get a call_id back
        if 'call_id' in response.json():
        
            print(f"Reminder call initiated successfully: {response.json()['call_id']} for {description}")
        else:
            print(f"Error making reminder call: {response.text}")

    except Exception as e:
        print(f"Error in make_reminder_call: {e}")


@app.post("/action/restriction/{domain}")
async def check_restriction(domain: str, make_call: bool = True):
    """
    Check if a website is restricted for Chrome extension
    """
    print(f"Checking restriction for {domain}")
    restriction = action_collection.find_one({"domain": domain})

    if not restriction:
        return {"restricted": False}

    print(f"Restriction found: {restriction}")

    if make_call and restriction.get("phone"):
        try:
            # Make call using RetellAI
            call_payload = {
                "to_number": restriction["phone"],
                "from_number": RETELL_PHONE_NUMBER,
                "override_agent_id": AGENT_ID_RESTRICTION,
                "retell_llm_dynamic_variables": {
                "reminder_description": {restriction.get("domain")}
            }

            }

            response = requests.post(
                "https://api.retellai.com/v2/create-phone-call",
                headers=app.state.retell_headers,
                json=call_payload,
            )

            if 'call_id' in response.json():
                print(f"Restriction notification call initiated successfully: {response.json()['call_id']}")
            else:
                print(f"Error making restriction notification call: {response.text}")

        except Exception as e:
            print(f"Error making restriction notification call: {e}")

    return {"restricted": True, "description": restriction.get("description")}




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
