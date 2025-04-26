import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

import requests
import ngrok
import pymongo
from pymongo import MongoClient
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

# Initialize MongoDB
client = MongoClient(MONGODB_URI)
db = client.get_database("La-Hacks")
action_collection = db.get_collection("action_restrictions")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# def schedule_reminder_call(action_id, phone, date_str, time_str):
#     """Schedule a call for a reminder"""
#     try:
#         date_format = "%Y-%m-%d %H:%M"
#         call_time = datetime.strptime(f"{date_str} {time_str}", date_format)
        
#         # Check if the time is in the past
#         if call_time < datetime.now():
#             print(f"Warning: Reminder time {date_str} {time_str} is in the past, scheduling for 1 minute from now")
#             call_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
        
#         job_id = f"reminder_{action_id}"
#         # Check if job already exists
#         if job_id in [job.id for job in scheduler.get_jobs()]:
#             scheduler.remove_job(job_id)
        
#         # Add new job
#         scheduler.add_job(
#             call_reminder,
#             'date',
#             run_date=call_time,
#             args=[phone, str(action_id)],
#             id=job_id,
#             replace_existing=True
#         )
#         print(f"Scheduled reminder call for {phone} at {call_time}")
#         return job_id
#     except Exception as e:
#         print(f"Error scheduling reminder: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to schedule reminder: {str(e)}")

# def call_reminder(phone, action_id):
#     """Make the actual reminder call using Twilio"""
#     try:
#         # Get the action details from MongoDB
#         action = action_collection.find_one({"_id": pymongo.ObjectId(action_id)})
#         if not action:
#             print(f"Warning: Action {action_id} not found when executing reminder")
#             return
        
#         # Add a query parameter with the action_id for the TwiML endpoint
#         twiml_endpoint = f"http://localhost:8080/twiml?action_id={action_id}"
        
#         # This will use the existing /call endpoint with the action-specific TwiML
#         response = requests.post(
#             f"http://localhost:8080/call?phone={phone}&twiml_url={twiml_endpoint}"
#         )
#         print(f"Reminder call initiated for action {action_id}: {response.status_code}")
#     except Exception as e:
#         print(f"Error making reminder call: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global NGROK_PUBLIC_URL
    listener = await ngrok.forward(8080, authtoken_from_env=True)
    app.state.ngrok = listener
    yield
    listener.close()


app = FastAPI(lifespan=lifespan)



class BrowserUsage(BaseModel):
    date: str
    email: str
    domain: str
    active_time: int


                # @app.post("/usage")
                # async def usage(usage: BrowserUsage):
                #     print(f"Received usage data: {usage}")
                #     return {"message": "Usage data received!"}


# @app.post("/call")
# def call(phone: str, twiml_url: Optional[str] = None):
#     """Initiate a call using Twilio"""
#     # Use provided TwiML URL or default to our base TwiML endpoint
#     if not twiml_url:
#         twiml_url = f"{app.state.ngrok.url()}/twiml"
    
#     payload = {
#         "Url": twiml_url,
#         "To": phone,
#         "From": TWILIO_PHONE_NUMBER,
#     }
    
#     try:
#         resp = requests.post(
#             f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Calls.json",
#             data=payload,
#             auth=(ACCOUNT_SID, AUTH_TOKEN),
#         )
#         print(f"Call status: {resp.status_code}")
#         if resp.status_code >= 400:
#             print(f"Call error: {resp.text}")
#             return {"success": False, "message": f"Failed to initiate call: {resp.text}"}
#         return {"success": True, "message": "Call initiated!"}
#     except Exception as e:
#         print(f"Error initiating call: {e}")
#         return {"success": False, "message": f"Error: {str(e)}"}


# @app.websocket("/")
# async def websocket_endpoint(ws: WebSocket):
    
#     await ws.accept()
#     while True:
#         data = await ws.receive_bytes()
#         # TODO: Process the call data


# @app.get("/twiml")
# async def twiml(action_id: Optional[str] = None):
#     """Return TwiML for the call, optionally customized for a specific action"""
#     try:
#         message = "This is a reminder from your personal assistant."
        
#         # If action_id is provided, get the action details from MongoDB
#         if action_id:
#             action = action_collection.find_one({"_id": pymongo.ObjectId(action_id)})
#             if action:
#                 message = f"This is a reminder from your personal assistant about: {action['description']}"
        
#         twiml_response = f"""
#         <?xml version="1.0" encoding="UTF-8"?>
#         <Response>
#             <Say>{message}</Say>
#             <Pause length="1"/>
#             <Say>Thank you for using our service. Goodbye.</Say>
#         </Response>
#         """
#         return Response(content=twiml_response, media_type="application/xml")
#     except Exception as e:
#         print(f"Error generating TwiML: {e}")
#         # Return a default TwiML in case of error
#         default_twiml = """
#         <?xml version="1.0" encoding="UTF-8"?>
#         <Response>
#             <Say>This is a reminder from your personal assistant.</Say>
#             <Say>Thank you for using our service. Goodbye.</Say>
#         </Response>
#         """
#         return Response(content=default_twiml, media_type="application/xml")


class ActionType(str, Enum):
    RESTRICTION = "restriction"
    REMINDER = "reminder"


# New models and endpoints for the action feature
class ActionBase(BaseModel):
    date: str
    time: str
    website: Optional[str] = None
    description: str
    type: ActionType
    phone: Optional[str] = None  # Phone number for reminders


class ActionCreate(ActionBase):
    pass


class Action(ActionBase):
    id: str


# @app.post("/action", response_model=Action)
# async def create_action(action: ActionCreate):
#     """Create a new action (restriction or reminder)"""
#     # Convert model to dict
#     action_dict = action.model_dump()
    
#     # Validate based on type
#     if action.type == ActionType.REMINDER and not action.phone:
#         raise HTTPException(status_code=400, detail="Phone number is required for reminders")
    
#     if action.type == ActionType.RESTRICTION and not action.website:
#         raise HTTPException(status_code=400, detail="Website is required for restrictions")
    
#     # Insert into MongoDB
#     result = action_collection.insert_one(action_dict)
#     action_id = str(result.inserted_id)
    
#     # If it's a reminder, schedule the call
#     if action.type == ActionType.REMINDER:
#         schedule_reminder_call(action_id, action.phone, action.date, action.time)
    
#     # Return the created action with its ID
#     return {**action_dict, "id": action_id}


# @app.get("/action")
# async def get_actions():
#     """Get all actions"""
#     actions = list(action_collection.find())
#     # Convert ObjectId to str for JSON serialization
#     for action in actions:
#         action["id"] = str(action.pop("_id"))
#     return actions


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
        "created_at": datetime.now().isoformat()
    }
    
    result = action_collection.insert_one(reminder)
    reminder_id = str(result.inserted_id)
    
    # Schedule the reminder
    try:
        date_format = "%Y-%m-%d %H:%M"
        scheduled_time = datetime.strptime(f"{date} {time}", date_format)
        
        
        job_id = f"reminder_{reminder_id}"
        
        scheduler.add_job(
            make_reminder_call,
            'date',
            run_date=scheduled_time,
            args=[phone, reminder_id, description],
            id=job_id,
            replace_existing=True
        )
        
        return {
            "success": True,
            "message": f"Reminder created and scheduled for {date} {time}",
            "id": reminder_id,
            "scheduled_time": scheduled_time.isoformat()
        }
    except ValueError:
        return {
            "success": False,
            "message": f"Invalid date or time format: {date} {time}. Use YYYY-MM-DD and HH:MM formats.",
            "id": reminder_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error scheduling reminder: {str(e)}",
            "id": reminder_id
        }



# Add this function for scheduling reminders
def schedule_jobs_from_database():
    """
    Load all reminders from the database and schedule them
    """
    print("Scheduling jobs from database...")
    reminders = list(action_collection.find({"type": "reminder"}))
    scheduled_count = 0
    
    for reminder in reminders:
        try:
            reminder_id = str(reminder["_id"])
            date_str = reminder.get("date")
            time_str = reminder.get("time")
            phone = reminder.get("phone")
            
            if not all([date_str, time_str, phone]):
                print(f"Warning: Reminder {reminder_id} missing required fields")
                continue
                
            # Parse the date and time
            date_format = "%Y-%m-%d %H:%M"
            try:
                scheduled_time = datetime.strptime(f"{date_str} {time_str}", date_format)
            except ValueError:
                print(f"Warning: Could not parse date/time for reminder {reminder_id}: {date_str} {time_str}")
                continue
                
            # Check if the time is in the past
            if scheduled_time < datetime.now():
                # Skip past reminders or reschedule them if needed
                print(f"Warning: Reminder {reminder_id} scheduled for {date_str} {time_str} is in the past")
                continue
                
            # Create a job ID
            job_id = f"reminder_{reminder_id}"
            
            # Remove existing job if it exists
            if job_id in [job.id for job in scheduler.get_jobs()]:
                scheduler.remove_job(job_id)
                
            # Schedule the job
            scheduler.add_job(
                make_reminder_call,
                'date',
                run_date=scheduled_time,
                args=[phone, reminder_id, reminder.get("description", "your scheduled reminder")],
                id=job_id,
                replace_existing=True
            )
            scheduled_count += 1
            print(f"Scheduled reminder {reminder_id} for {date_str} {time_str}")
            
        except Exception as e:
            print(f"Error scheduling reminder {reminder.get('_id')}: {e}")
    
    print(f"Scheduled {scheduled_count} reminders from database")
    return scheduled_count

# Function to make the actual call
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
        
        # Make the call using Twilio
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
        
        print(f"Reminder call result: status={resp.status_code}")
        
        # Update the reminder in the database if needed
        # For example, mark it as completed or record the call status
        action_collection.update_one(
            {"_id": pymongo.ObjectId(reminder_id)},
            {"$set": {"last_called": datetime.now().isoformat(), "call_status": resp.status_code}}
        )
        
    except Exception as e:
        print(f"Error making reminder call: {e}")

# Update the create_reminder function to schedule jobs

# Add endpoint to view all scheduled jobs


# Load all reminders from database on startup
@app.on_event("startup")
async def startup_scheduler():
    """
    Load all reminders from the database on startup
    """
    schedule_jobs_from_database()

@app.post("/call-phone")
async def call_phone(phone: str):
    """
    Make a direct call to a phone number
    """
    twiml_endpoint = f"{app.state.ngrok.url()}/twiml"
    payload = {
        "Url": twiml_endpoint,
        "To": phone,
        "From": TWILIO_PHONE_NUMBER,
    }
    
    try:
        resp = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Calls.json",
            data=payload,
            auth=(ACCOUNT_SID, AUTH_TOKEN),
        )
        return {
            "success": resp.status_code < 400,
            "status_code": resp.status_code,
            "message": "Call initiated successfully" if resp.status_code < 400 else f"Failed to make call: {resp.text}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }
    




    ## JUST FOR tesTING



@app.get("/scheduler/jobs")
async def list_scheduled_jobs():
    """
    List all scheduled jobs in the scheduler
    """
    jobs = scheduler.get_jobs()
    job_details = []
    
    for job in jobs:
        job_details.append({
            "id": job.id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "function": job.func.__name__
        })
    
    return {
        "total_jobs": len(job_details),
        "jobs": job_details
    }