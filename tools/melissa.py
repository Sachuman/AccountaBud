

## GET THE LOCATION OF THE USER


## HOSPITAL LOCATION, BASED ON THE LOCATION AND DESCRIPTION.
##  SEND THE SCHEMA TO MONOGDB
## WITH THE HOSPITAL NAME, LATITUDE, LONGITUDE, DESCRIPTION.

## FRONTEND MARK THE HOSPITAL ON THE MAP WITH DESCRIPTION and use case. while location current user location.

import os
import datetime
from contextlib import asynccontextmanager

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
MONGO_URL = os.getenv("MONGO_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MELISSA_KEY = os.getenv("MELISSA_KEY")  # Melissa API key

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client.get_database("La-Hacks")
location_collection = db.get_collection("user_location")
hospitals_collection = db.get_collection("hospitals")
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


class LocationRequest(BaseModel):
    latitude: float
    longitude: float


class TranscriptRequest(BaseModel):
    transcript: str


@app.post("/user-location")
async def set_location(data: LocationRequest):
    """
    Stores or updates the user's current location
    """
    # Upsert user (single user assumed)
    location_collection.replace_one(
        {"_id": "current_user"},
        {"_id": "current_user", "latitude": data.latitude, "longitude": data.longitude, "updated_at": datetime.datetime.utcnow()},
        upsert=True
    )
    return {"status": "location saved"}


@app.get("/hospitals")
async def get_hospitals(level: str = "basic"):
    """
    Retrieves nearby healthcare facilities based on the level:
    basic: hospitals only
    deep: hospitals + hours (trauma not available)
    advanced: all healthcare related services
    """
    # Retrieve user location
    loc = location_collection.find_one({"_id": "current_user"})
    if not loc:
        raise HTTPException(status_code=400, detail="User location not set")

    lat = loc["latitude"]
    lon = loc["longitude"]
    # Call Melissa Reverse GeoCoder to get nearby addresses
    revgeo_url = "https://reversegeo.melissadata.net/V3/WEB/ReverseGeoCode/doLookup"
    params = {
        "id": MELISSA_KEY,
        "Latitude": lat,
        "Longitude": lon,
        "MaxDistance": 10,  # miles
        "MaxRecords": 50,
        "format": "json"
    }
    resp = requests.get(revgeo_url, params=params)
    resp.raise_for_status()
    addresses = resp.json().get("Records", [])

    hospitals = []
    for addr in addresses:
        # Build address string
        a1 = addr.get("AddressLine1")
        city = addr.get("City")
        st = addr.get("StateProvince")
        postal = addr.get("PostalCode")
        # Lookup property to filter hospitals/clinics
        prop_url = "https://property.melissadata.net/v4/WEB/LookupProperty"
        prop_params = {
            "id": MELISSA_KEY,
            "a1": a1,
            "city": city,
            "state": st,
            "postal": postal,
            "format": "json"
        }
        p = requests.get(prop_url, params=prop_params).json()
        use = p.get("PropertyUseStandardized", "")
        # Filter based on level
        if level == "basic" and "Hospital" not in use:
            continue
        # Advanced: include clinics, pharmacies
        if level == "advanced":
            # accept Hospital, Clinic, Pharmacy in use
            if not any(x in use for x in ["Hospital", "Clinic", "Pharmacy"]):
                continue
        # Deep: same as basic (hours not in Melissa)
        # Construct record
        rec = {
            "name": addr.get("PlaceName", ""),
            "latitude": addr.get("Latitude"),
            "longitude": addr.get("Longitude"),
            "use": use
        }
        hospitals.append(rec)
    # Store in Mongo
    hospitals_collection.delete_many({})
    hospitals_collection.insert_many(hospitals)
    return {"count": len(hospitals), "hospitals": hospitals}

# ... existing endpoints for process-transcript, restrictions, reminders unchanged ...

# At frontend: fetch /hospitals?level=advanced and plot on map using returned list

