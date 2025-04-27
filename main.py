import os
import datetime
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, Request
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
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
AGENT_NAME = os.getenv("AGENT_NAME", "")  # Default to empty string if not set

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client.get_database("La-Hacks")
action_collection = db.get_collection("action_restrictions")
reminder_collection = db.get_collection("action_reminders")


# Initialize scheduler for reminders
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
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


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.post("/call")
async def make_call(request: Request):
    to_number = (await request.json()).get("to_number")

    if not to_number:
        return {"status": "error", "message": "No phone number provided"}

    print(f"Making call to {to_number}")

    call_payload = {
        "to_number": to_number,
        "from_number": RETELL_PHONE_NUMBER,
    }

    response = requests.post(
        "https://api.retellai.com/v2/create-phone-call",
        headers=app.state.retell_headers,
        json=call_payload,
    )

    if response.status_code == 200:
        call_id = response.json().get("call_id")
        return {"status": "success", "call_id": call_id}


class BrowserUsage(BaseModel):
    date: str
    email: str
    hostname: str
    active_sec: int


@app.post("/browser-usage")
async def browser_usage(data: list[BrowserUsage]):
    for usage in data:
        res = await check_restriction(usage.hostname)
        if res["restricted"]:
            return {"notified": True, "hostname": usage.hostname}

    return {"notified": False}


class TranscriptRequest(BaseModel):
    transcript: str


async def process_transcript(transcript: str, user_phone: str = None):
    """
    Process transcript using Gemini to determine intent and structure
    """
    now = datetime.datetime.now().isoformat()
    prompt = f"""
Analyze the following transcript from a phone call and determine if it's for:
1. Setting a restriction on a website
2. Setting a reminder for a task

THERE ARE CAN BE MULTIPLE RESTRICTIONS AND REMINDERS IN THE TRANSCRIPT. PLEASE REVIEW AND RETURN ALL OF THEM.
UNDERSTAND what user wants, identify all reminders and it can have multiple times. identify all restrictions and it can have multiple hostnames.
we need json for each restriction and reminder. If there is a daily event, create multiple reminders for each day.

If it's a restriction, extract:
- hostname (the website to restrict)
- description (reason for restriction)
- phone number

If it's a reminder, extract:
- date (in YYYY-MM-DD format, use today's date if not specified)
- time (in HH:MM format)
- description (what to remind about)
- phone number

RESPOND ONLY WITH A VALID JSON OBJECT. Do not include any explanations, markdown formatting, or code blocks.
The JSON must have a "type" field that is either "restriction" or "reminder", plus the other extracted fields.

The user's phone number is {user_phone}. Today's date is {now}.
Example response for a reminder:
{{"type": "reminder", "date": "2023-04-15", "time": "07:00", "description": "Wake up call", "phone": "+1234567890"}}

Example response for a restriction:
{{"type": "restriction", "hostname": "www.facebook.com", "description": "Avoid social media", "phone": "+1234567890"}}

Transcript: {transcript}
"""

    try:
        response = app.state.gemini_model.generate_content(prompt)
        response_text = response.text
        parser = JsonOutputParser()
        result = parser.parse(response_text)

        assert isinstance(result, list), "Response should be a list of JSON objects"

        for item in result:
            # Add current date and timestamp
            item["created_at"] = now

            if item["type"] == "restriction":
                # Store restriction in database
                action_collection.insert_one(item)
                print(f"Stored new restriction: {item}")

            elif item["type"] == "reminder":
                # Store reminder in database
                reminder_collection.insert_one(item).inserted_id

                # Schedule reminder if time is specified
                if item.get("time") and item.get("phone"):
                    schedule_reminder(
                        item["date"],
                        item["time"],
                        item["phone"],
                        item["description"],
                    )
                    print(f"Scheduled reminder: {item}")

    except Exception as e:
        print(f"Error prompting Gemini: {e}")
        result = []

    return str(result)


def schedule_reminder(date_str: str, time_str: str, phone: str, description: str):
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
            trigger="date",
            run_date=reminder_datetime,
            args=[phone, description],
        )
    except Exception as e:
        print(f"Error scheduling reminder: {e}")


async def make_reminder_call(phone: str, description: str):
    """
    Make a call to remind the user
    """
    try:
        # Request body for RetellAI call API
        call_payload = {
            "to_number": phone,
            "from_number": RETELL_PHONE_NUMBER,
            "override_agent_id": AGENT_ID_REMINDER,
            "retell_llm_dynamic_variables": {"reminder_description": description},
        }

        # Make API call to RetellAI
        response = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers=app.state.retell_headers,
            json=call_payload,
        )

        # The response is successful if we get a call_id back
        if "call_id" in response.json():
            print(
                f"Reminder call initiated successfully: {response.json()['call_id']} for {description}"
            )
        else:
            print(f"Error making reminder call: {response.text}")

    except Exception as e:
        print(f"Error in make_reminder_call: {e}")


@app.post("/action/restriction/{hostname}")
async def check_restriction(hostname: str, make_call: bool = True):
    """
    Check if a website is restricted for Chrome extension
    """
    print(f"Checking restriction for {hostname}")
    restriction = action_collection.find_one({"hostname": hostname})

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
                    "restriction_description": restriction.get("hostname")
                },
            }

            response = requests.post(
                "https://api.retellai.com/v2/create-phone-call",
                headers=app.state.retell_headers,
                json=call_payload,
            )

            if "call_id" in response.json():
                print(
                    f"Restriction notification call initiated successfully: {response.json()['call_id']}"
                )
            else:
                print(f"Error making restriction notification call: {response.text}")

        except Exception as e:
            print(f"Error making restriction notification call: {e}")

    return {"restricted": True, "description": restriction.get("description")}


@app.post("/action/process-example")
async def process_example():
    """
    Process example transcript for testing
    """
    # Example transcript
    transcript = """
Agent: Hi [Name], this is Sam from WakeUp Together. How are you doing today?
User: Okay. Well,
Agent: Great! I'm calling to help you create a schedule that supports your long-term goals. To start, could you share some of those goals with me? What are you working toward or hoping to change?
User: I'd like to record every day. I want to commit some call to get up every single day.
User: Yeah. That'll be nice.
Agent: That's a great goal! What kind of daily or weekly structure would help you feel more supported in recording every day and getting up consistently?
User: No. I said I wanted to connect to GitHub every day.
Agent: Thanks for the clarification! What kind of daily or weekly structure would help you feel more supported in connecting to GitHub every day and getting up consistently?
User: No. Permitting code, if they don't.
Agent: Okay, thanks for clarifying. So, to make sure I understand, you want to commit code to GitHub every day and get up consistently. What kind of daily or weekly structure would help you feel more supported in achieving those goals?
User: Yeah. I I think, I think I'd like to be given a reminder.
User: one PM every day to talk to GitHub. Uh, to to commit for to GitHub.
Agent: Got it! Would you like to set up some regular call times to stay on track with committing to GitHub around 1 PM each day? Would mornings or evenings be better for you for check-in calls?
User: Yeah. So every every evening, I want to get a one I have I wanna get a one PM calls every day.
User: Asking me if I've committed any port to GitHub yet. And if I haven't done that yet, then I'd like to then, like, you could give me ideas project ideas that I could work on today.
User: And get me going.
Agent: Okay, great! So, we'll have a call every day around 1 PM to check on your GitHub commits and brainstorm project ideas if needed. Want to start this Thursday morning?
User: I wanna start from day one. Like, I wanna do it every day Like, I wanna do it from the very next one PM.
Agent: Perfect! So we'll start tomorrow at 1 PM. Just a reminder that this schedule is completely flexible and can be adjusted anytime to fit your life. Do you have any questions or anything else you'd like to add?
User: Yeah. I think I'd also want a wake up call every day at six AM.
Agent: Got it. So, in addition to the 1 PM call for GitHub, you'd also like a wake-up call every day at 6 AM. Is that right?
User: Yeah. Pretty much
User: And then, actually, finally, on Friday, could you call me at eight PM and, um, check if I've completed my assignments?
Agent: Okay, so let's make sure I have this right: a 6 AM wake-up call every day, a 1 PM call to check on your GitHub commits, and a call on Fridays at 8 PM to check on your assignments. Is that all correct?
User: Yes. That sounds good.
Agent: Great! Just a reminder that this schedule is completely flexible and can be adjusted anytime to fit your life. Do you have any questions or anything else you'd like to add?
User: No. I think that's it.
Agent: Wonderful! I'm excited to help you stay on track. I'll go ahead and wrap things up. Have a productive day, and I'll talk to you tomorrow!
    """

    await process_transcript(transcript)


# Webhook route to receive call completion notifications
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if data["event"] != "call_analyzed":
        return {"status": "skipped"}

    call_id = data.get("call_id")
    print(f"Call analyzed notification received for call ID: {call_id}")
    transcript = data["call"]["transcript"]
    user_phone = data["call"]["from_number"]
    print(f"Transcript: {transcript}")

    if "voicemail" in transcript.lower() or "voice mail" in transcript.lower():
        description = (
            "checking in with their accountability buddy who did not respond to"
            "their reminder call."
        )
        call_payload = {
            "to_number": "+19493072284",
            "from_number": RETELL_PHONE_NUMBER,
            "override_agent_id": AGENT_ID_REMINDER,
            "retell_llm_dynamic_variables": {"reminder_description": description},
        }
        response = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers=app.state.retell_headers,
            json=call_payload,
        )
        if response.status_code == 200:
            print("Voicemail detected, call made to +19493072284")
        else:
            print(f"Error making call to +19493072284: {response.text}")
        return {"status": "skipped"}

    await process_transcript(transcript, user_phone)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
