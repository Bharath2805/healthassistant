# backend/doctor_search.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import logging
import asyncio
import difflib
from dotenv import load_dotenv
import os
from datetime import datetime
from backend.auth.schemas import User
from backend.auth.auth import get_current_user
from backend.database import get_db_connection

load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
logger = logging.getLogger(__name__)

router = APIRouter()

# Extended specialty mapping
SPECIALTY_MAPPING = {
    "knee": "Orthopedist",
    "bone": "Orthopedist",
    "heart": "Cardiologist",
    "cardio": "Cardiologist",
    "skin": "Dermatologist",
    "derma": "Dermatologist",
    "headache": "Neurologist",
    "brain": "Neurologist",
    "lung": "Pulmonologist",
    "cancer": "Oncologist",
    "stomach": "Gastroenterologist",
    "eyes": "Ophthalmologist",
    "eye": "Ophthalmologist",
    "vision": "Ophthalmologist",
    "teeth": "Dentist",
    "tooth": "Dentist",
    "ear": "ENT",
    "throat": "ENT",
    "child": "Pediatrician",
    "woman": "Gynecologist",
    "pregnancy": "Gynecologist",
    "diabetes": "Endocrinologist",
    "hormone": "Endocrinologist",
    "muscle": "Physiotherapist",
    "mental": "Psychiatrist",
    "depression": "Psychiatrist",
}

# Pagination helper function - updated to allow larger page sizes
def get_safe_pagination(page: int, page_size: int, max_page_size: int = 1000):  # Changed from 50 to 1000
    safe_page = page if page > 0 else 1
    safe_page_size = min(page_size if page_size > 0 else 5, max_page_size)
    return safe_page, safe_page_size

# Helper function to fuzzy match specialty terms
def fuzzy_specialty_match(query: str) -> str:
    all_specialties = list(set(SPECIALTY_MAPPING.values()))
    match = difflib.get_close_matches(query, all_specialties, n=1, cutoff=0.6)
    if match:
        return match[0]
    # If no direct match, check the mapping keys
    for key, specialty in SPECIALTY_MAPPING.items():
        if key in query.lower():
            return specialty
    return query

# Request model for doctor search (used by search_doctor)
class DoctorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    from_health_assistant: Optional[bool] = False
    page: Optional[int] = 1
    page_size: Optional[int] = 100  # Changed from 5 to 100

# Request model for the /search-doctor endpoint
class DoctorSearchQuery(BaseModel):
    specialty: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    page: int = 1
    page_size: int = 100  # Changed from 10 to 100

# Helper function to get user location via IP geolocation
async def get_user_location() -> tuple[float, float]:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://ipapi.co/json/")
        data = response.json()
        return data.get("latitude"), data.get("longitude")

# Helper function to geocode a location string to latitude and longitude
async def geocode_location(location: str) -> tuple[float, float]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": location, "key": GOOGLE_PLACES_API_KEY}
        )
        data = response.json()
        if not data["results"]:
            raise HTTPException(status_code=400, detail="Invalid location")
        geometry = data["results"][0]["geometry"]["location"]
        return geometry["lat"], geometry["lng"]

# Fetch doctors using Google Places API - modified to get all results
async def fetch_doctors(specialty: str, latitude: float, longitude: float, all_results: bool = True):  # Changed default to True
    async with httpx.AsyncClient() as client:
        doctors = []
        next_page_token = None
        page_count = 0
        while True:
            params = {
                "key": GOOGLE_PLACES_API_KEY,
                "keyword": f"{specialty} doctor",
                "radius": 50000,  # Increased from 5000 to 50000 meters
                "location": f"{latitude},{longitude}"
            }
            if next_page_token:
                params["pagetoken"] = next_page_token
            response = await client.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params)
            results = response.json().get("results", [])
            for result in results:
                # Fetch additional details to get phone and website
                place_id = result.get("place_id")
                if place_id:
                    details_response = await client.get(
                        "https://maps.googleapis.com/maps/api/place/details/json",
                        params={"place_id": place_id, "fields": "name,formatted_phone_number,website", "key": GOOGLE_PLACES_API_KEY}
                    )
                    details = details_response.json().get("result", {})
                    
                    doctor = {
                        "name": result.get("name"),
                        "specialty": specialty,
                        "address": result.get("vicinity"),
                        "phone": details.get("formatted_phone_number"),
                        "website": details.get("website"),
                        "rating": result.get("rating"),
                        "place_id": place_id
                    }
                    doctors.append(doctor)
            
            next_page_token = response.json().get("next_page_token")
            page_count += 1
            
            # Limit to 3 pages (max ~60 results from Places API)
            if not next_page_token or not all_results or page_count >= 3:
                break
                
            await asyncio.sleep(2)  # Google API requires delay between page requests
        
        return doctors

# Existing doctor search function (used by health assistant)
async def search_doctor(request: DoctorSearchRequest, current_user: User = Depends(get_current_user)):
    user_id = str(current_user.id) if current_user.id else "anonymous"  # Convert UUID to string
    conn = await get_db_connection()
    try:
        # Check search limit for anonymous users
        if user_id == "anonymous":
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM doctor_searches WHERE user_id = $1", user_id
            )
            if count >= 2:
                raise HTTPException(status_code=403, detail="Please log in after 2 searches.")

        # Determine specialty based on query
        specialty = fuzzy_specialty_match(request.query)

        # Determine location
        if request.latitude is not None and request.longitude is not None:
            latitude, longitude = request.latitude, request.longitude
        elif request.location:
            latitude, longitude = await geocode_location(request.location)
        else:
            latitude, longitude = await get_user_location()

        # Fetch doctors - always get all results
        doctors = await fetch_doctors(specialty, latitude, longitude, all_results=True)
        total = len(doctors)

        # Apply pagination if not from health assistant
        if not request.from_health_assistant:
            page, page_size = get_safe_pagination(
                getattr(request, "page", 1),
                getattr(request, "page_size", 100)  # Changed from 5 to 100
            )
            start = (page - 1) * page_size
            end = start + page_size
            paginated_doctors = doctors[start:end]
        else:
            paginated_doctors = doctors
            page = page_size = None

        # Log the search in the database
        await conn.execute(
            "INSERT INTO doctor_searches (user_id, query, specialty, location, created_at) "
            "VALUES ($1, $2, $3, $4, $5)",
            user_id, request.query, specialty, f"{latitude},{longitude}", datetime.utcnow()
        )

        return {
            "specialty": specialty,
            "doctors": paginated_doctors,
            "pagination": None if request.from_health_assistant else {
                "current_page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0
            }
        }
    finally:
        await conn.close()

# Endpoint for searching doctors with pagination (POST)
@router.post("/search-doctor")
async def search_doctor_with_pagination(
    query: DoctorSearchQuery,
    current_user: User = Depends(get_current_user)
):
    specialty = fuzzy_specialty_match(query.specialty)
    
    # Determine coordinates
    if query.latitude and query.longitude:
        lat, lon = query.latitude, query.longitude
    elif query.location:
        lat, lon = await geocode_location(query.location)
    else:
        lat, lon = await get_user_location()

    # Fetch all doctors
    all_doctors = await fetch_doctors(specialty, lat, lon, all_results=True)

    # Apply pagination - with higher limits
    page, page_size = get_safe_pagination(query.page, query.page_size, max_page_size=1000)
    total = len(all_doctors)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_doctors[start:end]

    return {
        "specialty": specialty,
        "location": {"latitude": lat, "longitude": lon},
        "results": paginated,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }

# New GET endpoint for compatibility with /doctor-search
@router.get("/doctor-search")
async def doctor_search_get(
    specialty: str,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    page: int = 1,
    page_size: int = 100,  # Changed from 10 to 100
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Searching for doctors with specialty: {specialty} and location: {location}")
    specialty = fuzzy_specialty_match(specialty)
    
    # Determine coordinates
    if latitude and longitude:
        lat, lon = latitude, longitude
    elif location:
        lat, lon = await geocode_location(location)
    else:
        lat, lon = await get_user_location()

    # Fetch all doctors
    all_doctors = await fetch_doctors(specialty, lat, lon, all_results=True)

    # Apply pagination with higher limits
    page, page_size = get_safe_pagination(page, page_size, max_page_size=1000)
    total = len(all_doctors)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_doctors[start:end]

    return {
        "specialty": specialty,
        "location": {"latitude": lat, "longitude": lon},
        "results": paginated,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }