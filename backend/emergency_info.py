from fastapi import APIRouter
import httpx

router = APIRouter()

@router.get("/emergency-info")
async def get_emergency_info():
    async with httpx.AsyncClient() as client:
        ip_data = await client.get("https://ipapi.co/json/")
        location = ip_data.json()
        country = location.get("country_name", "Unknown")

    emergency_numbers = {
        "Germany": {"ambulance": "112", "fire": "112", "police": "110"},
        "India": {"ambulance": "102", "fire": "101", "police": "100"},
        "USA": {"ambulance": "911", "fire": "911", "police": "911"},
        "UK": {"ambulance": "999", "fire": "999", "police": "999"},
        "France": {"ambulance": "15", "fire": "18", "police": "17"},
        "Australia": {"ambulance": "000", "fire": "000", "police": "000"},
        "Canada": {"ambulance": "911", "fire": "911", "police": "911"},
        "Italy": {"ambulance": "118", "fire": "115", "police": "113"},
        "Spain": {"ambulance": "112", "fire": "112", "police": "112"},
        "Japan": {"ambulance": "119", "fire": "119", "police": "110"},
        "China": {"ambulance": "120", "fire": "119", "police": "110"},
        "Brazil": {"ambulance": "192", "fire": "193", "police": "190"},
        "Russia": {"ambulance": "103", "fire": "101", "police": "102"},
        "Mexico": {"ambulance": "065", "fire": "068", "police": "060"},
        "South Africa": {"ambulance": "10177", "fire": "10177", "police": "10111"},
        "Saudi Arabia": {"ambulance": "997", "fire": "998", "police": "999"},
        "UAE": {"ambulance": "998", "fire": "997", "police": "999"},
        "Pakistan": {"ambulance": "115", "fire": "16", "police": "15"},
        "Bangladesh": {"ambulance": "199", "fire": "199", "police": "999"},
        "Sri Lanka": {"ambulance": "1990", "fire": "110", "police": "119"},
        "Nepal": {"ambulance": "102", "fire": "101", "police": "100"},
        "Netherlands": {"ambulance": "112", "fire": "112", "police": "112"},
        "Belgium": {"ambulance": "112", "fire": "112", "police": "112"},
        "Sweden": {"ambulance": "112", "fire": "112", "police": "112"},
        "Norway": {"ambulance": "113", "fire": "110", "police": "112"},
        "Denmark": {"ambulance": "112", "fire": "112", "police": "112"},
        "Finland": {"ambulance": "112", "fire": "112", "police": "112"},
        "Poland": {"ambulance": "999", "fire": "998", "police": "997"},
        "Portugal": {"ambulance": "112", "fire": "112", "police": "112"},
        "Switzerland": {"ambulance": "144", "fire": "118", "police": "117"},
        "Austria": {"ambulance": "144", "fire": "122", "police": "133"},
        "Greece": {"ambulance": "166", "fire": "199", "police": "100"},
        "Turkey": {"ambulance": "112", "fire": "110", "police": "155"},
    }

    default_info = {"ambulance": "112", "fire": "112", "police": "112"}

    return {
        "country": country,
        "emergency": emergency_numbers.get(country, default_info)
    }
