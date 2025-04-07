from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import httpx
import os
from dotenv import load_dotenv

from backend.database import init_db
from backend.chat import chat, get_sessions, ChatRequest
from backend.doctor_search import router as doctor_router
from backend.image_analysis import router as image_router
from backend.health_assistant import router as health_router
from backend.auth.auth import get_current_user
from backend.auth.routes import router as auth_router
from backend.auth.schemas import User
from backend.emergency_info import router as emergency_router
from backend.models.reminders import ReminderCreate
from backend.services.reminders import (
    create_reminder, get_reminders, delete_reminder, get_reminder_history
)

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Configuration from environment variables
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Debug print (optional)
print(f"JWT_SECRET: {os.getenv('JWT_SECRET')}")
print(f"EMAIL_HOST: {os.getenv('EMAIL_HOST')}")
print(f"EMAIL_USER: {os.getenv('EMAIL_USER')}")

# FastAPI app
app = FastAPI(
    title="Health Assistant API",
    description="AI-powered health guidance platform",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Use dynamic FRONTEND_URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file upload
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup
@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("✅ Database initialized")

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Internal API Router
router = APIRouter()

# 🧠 AI Chat
@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user)):
    return await chat(request, current_user)

@router.get("/sessions")
async def sessions_endpoint(current_user: User = Depends(get_current_user)):
    return await get_sessions(current_user)

# 🗓️ Reminders
@router.post("/reminders")
async def create_reminder_endpoint(reminder: ReminderCreate, current_user: User = Depends(get_current_user)):
    return await create_reminder(reminder, current_user)

@router.get("/reminders")
async def get_reminders_endpoint(current_user: User = Depends(get_current_user)):
    return await get_reminders(current_user)

@router.delete("/reminders/{reminder_id}")
async def delete_reminder_endpoint(reminder_id: int, current_user: User = Depends(get_current_user)):
    return await delete_reminder(reminder_id, current_user)

@router.get("/reminder-history")
async def reminder_history_endpoint(current_user: User = Depends(get_current_user)):
    return await get_reminder_history(current_user)

# 🌍 Country via IP necropsy
async def get_user_country():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://ipapi.co/json/")
            return response.json().get("country_code", "US")
        except Exception as e:
            logger.error(f"Could not get country from IP: {e}")
            return "US"

# Include all routers
app.include_router(router)
app.include_router(auth_router)
app.include_router(health_router, prefix="/health", tags=["Health Assistant"])
app.include_router(doctor_router, prefix="/health", tags=["Doctor Search"])
app.include_router(emergency_router, prefix="/health", tags=["Emergency Info"])
app.include_router(image_router, prefix="/health", tags=["Image Analysis"])

# Run
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)