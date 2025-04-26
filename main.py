import os
import datetime
from contextlib import asynccontextmanager

import ngrok
import requests
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import google.generativeai as genai
from langchain_core.output_parsers import JsonOutputParser


load_dotenv()

# Environment variables
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
AGENT_ID = os.getenv("RETELL_AGENT_ID")
MONGO_URL = os.getenv("MONGO_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
        # Define initial message for the call
        initial_message = f"This is your reminder about: {description}"

        # Request body for RetellAI call API
        call_payload = {
            "agent_id": AGENT_ID,
            "customer_number": phone,
            "initial_message": initial_message,
        }

        # Make API call to RetellAI
        response = requests.post(
            "https://api.retellai.com/v1/calls",
            headers=app.state.retell_headers,
            json=call_payload,
        )

        if response.status_code == 200:
            # Update reminder status in database
            reminder_collection.update_one(
                {"_id": reminder_id},
                {
                    "$set": {
                        "status": "called",
                        "called_at": datetime.datetime.now().isoformat(),
                    }
                },
            )
            print(f"Made reminder call to {phone} about {description}")
        else:
            print(f"Error making reminder call: {response.text}")

    except Exception as e:
        print(f"Error in make_reminder_call: {e}")


@app.post("/action/reminder")
async def create_reminder(request: Request):
    """
    Create a new reminder
    """
    data = await request.json()

    # Validate data
    required_fields = ["date", "description"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    # Add created_at timestamp and type
    data["created_at"] = datetime.datetime.now().isoformat()
    data["type"] = "reminder"

    # Insert into database
    reminder_id = reminder_collection.insert_one(data).inserted_id

    # Schedule reminder if time is specified
    if data.get("time") and data.get("phone"):
        schedule_reminder(
            str(reminder_id),
            data["date"],
            data["time"],
            data["phone"],
            data["description"],
        )

    return {"message": "Reminder created", "id": str(reminder_id)}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
