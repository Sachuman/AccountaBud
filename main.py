import os
import json
import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, List

import ngrok
import requests
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import google.generativeai as genai


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
        "Authorization": f"Bearer {RETELL_API_KEY}"
    }
    
    # Setup Gemini model
    genai.configure(api_key=GEMINI_API_KEY)
    app.state.gemini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")


    
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
async def process_transcript_endpoint(data: TranscriptRequest, background_tasks: BackgroundTasks):
    """
    Process transcript using Gemini and store in database
    """
    background_tasks.add_task(process_transcript, data.transcript)
    return {"status": "processing"}

async def process_transcript(transcript: str):
    """
    Process transcript using Gemini to determine intent and structure
    """
    prompt = f"""
    Analyze the following transcript from a phone call and determine if it's for:
    1. Setting a restriction on a website
    2. Setting a reminder for a task
    
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
    The JSON must have a "type" field that is either "RESTRICTION" or "reminder", plus the other extracted fields.
    
    Example response for a reminder:
    {{"type": "reminder", "date": "2023-04-15", "time": "07:00", "description": "Wake up call", "phone": "+1234567890"}}
    
    Example response for a restriction:
    {{"type": "RESTRICTION", "domain": "facebook.com", "description": "Avoid social media", "phone": "+1234567890"}}
    
    Transcript: {transcript}
    """
    
    try:
        response = app.state.gemini_model.generate_content(prompt)
        
        response_text = response.text
        
        import re
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group(1))
        else:
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:

                cleaned_text = response_text.strip()
                start = cleaned_text.find('{')
                end = cleaned_text.rfind('}') + 1
                
                if start >= 0 and end > start:
                    json_str = cleaned_text[start:end]
                    result = json.loads(json_str)
                else:
                    
                    print(f"Could not parse JSON from response: {response_text}")
                    result = {
                        "type": "unknown",
                        "description": "Failed to parse response",
                        "raw_response": response_text[:200] 
                    }
        
        # Add current date and timestamp
        result["created_at"] = datetime.datetime.now().isoformat()
        
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
                    result["description"]
                )
                print(f"Scheduled reminder: {result}")
        
    except Exception as e:
        print(f"Error processing transcript: {e}")
        print(f"Response text: {response.text if 'response' in locals() else 'No response'}")

def schedule_reminder(reminder_id: str, date_str: str, time_str: str, phone: str, description: str):
    """
    Schedule a reminder call
    """
    try:
        # Parse date and time
        reminder_datetime = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        # Add job to scheduler
        scheduler.add_job(
            make_reminder_call,
            'date',
            run_date=reminder_datetime,
            args=[reminder_id, phone, description]
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
            "initial_message": initial_message
        }
        
        # Make API call to RetellAI
        response = requests.post(
            "https://api.retellai.com/v1/calls",
            headers=app.state.retell_headers,
            json=call_payload
        )
        
        if response.status_code == 200:
            # Update reminder status in database
            reminder_collection.update_one(
                {"_id": reminder_id},
                {"$set": {"status": "called", "called_at": datetime.datetime.now().isoformat()}}
            )
            print(f"Made reminder call to {phone} about {description}")
        else:
            print(f"Error making reminder call: {response.text}")
            
    except Exception as e:
        print(f"Error in make_reminder_call: {e}")

# @app.get("/action/restriction/{domain}")
# async def check_restriction(domain: str, make_call: bool = True):
#     """
#     Check if a website is restricted for Chrome extension
#     """
#     print(f"Checking restriction for {domain}")
#     restriction = action_collection.find_one({"domain": domain})
    
#     if not restriction:
#         return {"restricted": False}
    
#     print(f"Restriction found: {restriction}")
    
#     # If restriction exists and call should be made
#     if make_call and restriction.get("phone"):
#         try:
#             # Make call using RetellAI
#             call_payload = {
#                 "agent_id": AGENT_ID,
#                 "customer_number": restriction["phone"],
#                 "initial_message": f"This is a reminder that {domain} is restricted. Reason: {restriction.get('description', 'Not specified')}"
#             }
            
#             response = requests.post(
#                 "https://api.retellai.com/v1/calls",
#                 headers=app.state.retell_headers,
#                 json=call_payload
#             )
            
#             if response.status_code != 200:
#                 print(f"Error making restriction notification call: {response.text}")
        
#         except Exception as e:
#             print(f"Error making restriction notification call: {e}")
    
#     return {"restricted": True, "description": restriction.get("description")}

@app.post("/action/restriction")
async def create_restriction(request: Request):
    """
    Create a new restriction
    """
    data = await request.json()
    
    # Validate data
    required_fields = ["domain", "description"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Add created_at timestamp and type
    data["created_at"] = datetime.datetime.now().isoformat()
    data["type"] = "RESTRICTION"
    
    # Insert into database
    restriction_id = action_collection.insert_one(data).inserted_id
    
    return {"message": "Restriction created", "id": str(restriction_id)}

# @app.get("/action/reminder/{date}")
# async def get_reminders(date: str):
#     """
#     Get all reminders for a specific date
#     """
#     reminders = list(reminder_collection.find({"date": date}))
    
#     # Convert ObjectId to string for JSON serialization
#     for reminder in reminders:
#         reminder["_id"] = str(reminder["_id"])
    
#     return {"reminders": reminders}

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
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
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
            data["description"]
        )
    
    return {"message": "Reminder created", "id": str(reminder_id)}

@app.post("/action/process-example")
async def process_example():
    """
    Process example transcript for testing
    """
    # Example transcript
    transcript = """
    Agent: Hey [Name], it's Sam from WakeUp Together! I'm calling to help you stay on track with your goal of waking up at 5:30am every day. Would you like me to call you around that time daily to check in?
    User: Yes. That would work.
    Agent: Awesome! Should we kick 
    User: Wait. Actually, no. 
    Agent: it off tomorrow morning, 
    User: Hold on. Can you call me at seven AM every day?
    Agent: No problem! So, you'd like me to call you at 7:00 AM every day instead?
    User: Yeah. That would be great.
    Agent: Perfect! Should we start tomorrow morning, then?
    User: Yeah. Sounds good. Thanks. Bye bye.
    Agent: Okay, great! Would you like the call to be a quick pep talk, like a
    """
    
    await process_transcript(transcript)
    return {"message": "Example transcript processed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)