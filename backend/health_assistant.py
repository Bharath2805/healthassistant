from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List
from backend.database import get_db_connection
from openai import AsyncOpenAI
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import logging
import json
from backend.auth.schemas import User
from backend.auth.auth import get_current_user
import re
from backend.doctor_search import fetch_doctors

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

router = APIRouter()

def clean_response(text: str) -> str:
    return re.sub(r"[*_`#>-]", "", text).strip()

# -------------------- MODELS --------------------
class SymptomRequest(BaseModel):
    symptoms: List[str]

class HealthResponse(BaseModel):
    diagnosis: str
    description: str
    severity: str
    recommended_speciality: str
    confidence: float

class GeneralQueryRequest(BaseModel):
    message: str

class DrugInteractionRequest(BaseModel):
    drugs: List[str]

class DrugInteractionDetail(BaseModel):
    drug_1: str
    drug_2: str
    risk: str
    description: str
    action: str

class DrugInteractionResponse(BaseModel):
    interactions: List[DrugInteractionDetail]
    overall_risk: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

async def get_user_location() -> tuple[float, float]:
    return 40.7128, -74.0060

def is_session_expired(created_at: datetime, minutes: int = 60) -> bool:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - created_at).total_seconds() > minutes * 60

async def analyze_symptoms(symptoms: List[str], user: User) -> dict:
    if not symptoms or not all(isinstance(s, str) and s.strip() for s in symptoms):
        raise HTTPException(status_code=422, detail="Symptoms must be a non-empty list of non-empty strings")
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a medical diagnostic expert. Provide a structured diagnosis based on symptoms in the format: Diagnosis: [text]\nDescription: [text]\nSeverity: [low/moderate/high]\nSpecialty: [text]\nConfidence: [0-1]."},
            {"role": "user", "content": f"Symptoms: {', '.join(symptoms)}"}
        ],
        max_tokens=500
    )
    text = response.choices[0].message.content.strip()
    lines = text.split("\n")
    diagnosis = lines[0].replace("Diagnosis: ", "") if "Diagnosis" in lines[0] else "Possible condition unclear"
    description = next((l for l in lines if "Description" in l), "Description: Further evaluation needed").replace("Description: ", "")
    severity = next((l for l in lines if "Severity" in l), "Severity: moderate").replace("Severity: ", "")
    specialty = next((l for l in lines if "Specialty" in l), "Specialty: General Practitioner").replace("Specialty: ", "")
    confidence = float(next((l for l in lines if "Confidence" in l), "Confidence: 0.5").replace("Confidence: ", ""))
    health_data = HealthResponse(diagnosis=diagnosis, description=description, severity=severity, recommended_speciality=specialty, confidence=confidence)
    
    doctor_suggestions = []
    if health_data.severity.lower() == "high":
        try:
            lat, lon = await get_user_location()
            doctor_suggestions = await fetch_doctors(
                specialty=health_data.recommended_speciality,
                latitude=lat,
                longitude=lon,
                all_results=True
            )
        except Exception as e:
            logger.warning(f"Failed to fetch doctors: {str(e)}")
    return {
        "diagnosis": health_data,
        "suggested_doctors": doctor_suggestions
    }

async def handle_general_query(request: GeneralQueryRequest, current_user: User, force_new: bool = False):
    message = request.message.strip()
    conn = await get_db_connection()

    try:
        existing_session = None
        if not force_new:
            existing_session = await conn.fetchrow(
                "SELECT id, created_at FROM sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
                str(current_user.id)
            )

        if existing_session and not is_session_expired(existing_session["created_at"]):
            session_id = str(existing_session["id"])
            logger.info(f"Reusing session: {session_id}")
        else:
            session_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO sessions (id, user_id, session_name, response_format, created_at) VALUES ($1, $2, $3, $4, $5)",
                session_id, str(current_user.id), f"General Query {datetime.utcnow()}", "Friendly Chat", datetime.utcnow()
            )
            logger.info(f"Created new session: {session_id}")

        prompt = (
            "You are a health assistant. Determine if the message is about a medicine, symptoms, or something else.\n"
            "Respond in this format:\n"
            "Category: [medicine/symptom/general]\n"
            "Content: [Give a helpful answer. If it's a medicine, include common usage and dosage.]"
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=500
        )

        output = response.choices[0].message.content.strip()
        lines = output.split("\n")
        category = next((l for l in lines if l.startswith("Category:")), "Category: general").replace("Category:", "").strip()
        content = next((l for l in lines if l.startswith("Content:")), "Content: Unable to understand").replace("Content:", "").strip()
        doctor_suggestions = []

        if category.lower() == "symptom":
            # Ask for structured response like diagnosis, severity, etc.
            structured = await openai_client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical expert. Based on the symptom, respond in the following format:\n"
                                   "Diagnosis: ...\nDescription: ...\nSeverity: low/moderate/high\nSpecialty: ...\nConfidence: 0.0-1.0"
                    },
                    {"role": "user", "content": message}
                ],
                max_tokens=500
            )

            text = structured.choices[0].message.content.strip()
            lines = text.split("\n")
            diagnosis = next((l.replace("Diagnosis: ", "") for l in lines if "Diagnosis:" in l), "Unknown")
            description = next((l.replace("Description: ", "") for l in lines if "Description:" in l), "No description.")
            severity = next((l.replace("Severity: ", "") for l in lines if "Severity:" in l), "moderate")
            specialty = next((l.replace("Specialty: ", "") for l in lines if "Specialty:" in l), "General Practitioner")
            confidence = float(next((l.replace("Confidence: ", "") for l in lines if "Confidence:" in l), "0.5"))

            # Final assistant message to show
            content = (
                f"Diagnosis: {diagnosis}\n"
                f"Description: {description}\n"
                f"Severity: {severity}\n"
                f"Recommended Specialist: {specialty}\n"
                f"Confidence: {round(confidence * 100)}%"
            )

            if severity.lower() == "high":
                try:
                    lat, lon = await get_user_location()
                    doctor_suggestions = await fetch_doctors(specialty, lat, lon, all_results=True)
                except Exception as e:
                    logger.warning(f"Doctor fetch failed: {e}")

        await conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES ($1, $2, $3, $4)",
            session_id, "user", message, datetime.utcnow()
        )
        await conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES ($1, $2, $3, $4)",
            session_id, "assistant", content, datetime.utcnow()
        )

        return {
            "session_id": session_id,
            "category": category,
            "response": content,
            "suggested_specialty": specialty if category.lower() == "symptom" else None,
            "high_severity": severity.lower() == "high" if category.lower() == "symptom" else False,
            "suggested_doctors": doctor_suggestions
        }

    except Exception as e:
        logger.error(f"Failed to process general query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process message")
    finally:
        await conn.close()

async def check_drug_interactions(request: DrugInteractionRequest, user: User) -> dict:
    if len(request.drugs) < 2:
        raise HTTPException(status_code=400, detail="Please provide at least two drugs to compare.")

    joined = ", ".join(request.drugs)
    system_prompt = (
        "You are a clinical pharmacist. Given a list of drugs, return structured JSON containing:\n"
        "1. interactions: list of interactions between drug pairs (drug_1, drug_2, risk, description, action)\n"
        "2. overall_risk: one of 'low', 'moderate', 'high'.\n"
        "Respond ONLY with JSON."
    )
    
    user_prompt = f"Check interactions between: {joined}"

    response = await openai_client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=600
    )

    raw_json = response.choices[0].message.content.strip()

    if raw_json.startswith("```json"):
         raw_json = raw_json.replace("```json", "").replace("```", "").strip()
    elif raw_json.startswith("```"):
         raw_json = raw_json.replace("```", "").strip()
    try:
        interaction_data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.error(f"OpenAI returned non-JSON output: {raw_json}")
        raise HTTPException(status_code=500, detail=f"Failed to parse JSON response from AI: {str(e)}")

    doctor_suggestions = []
    if interaction_data.get("overall_risk", "").lower() == "high":
        try:
            lat, lon = await get_user_location()
            doctor_suggestions = await fetch_doctors(
                specialty="General Practitioner",
                latitude=lat,
                longitude=lon,
                all_results=True
            )
        except Exception as e:
            logger.warning(f"Failed to fetch doctors for interaction: {str(e)}")
    
    return {
        "data": interaction_data,
        "suggested_doctors": doctor_suggestions
    }

# -------------------- ENDPOINTS --------------------
@router.post("/symptoms")
async def health_assistant_symptoms(request: SymptomRequest, current_user: User = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        existing_session = await conn.fetchrow(
            "SELECT id, created_at FROM sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
            str(current_user.id)
        )

        if existing_session and not is_session_expired(existing_session["created_at"]):
            session_id = str(existing_session["id"])
            logger.info(f"Reusing session: {session_id}")
        else:
            session_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO sessions (id, user_id, session_name, response_format, created_at) "
                "VALUES ($1, $2, $3, $4, $5)",
                session_id, str(current_user.id) if current_user.id is not None else None, f"Symptoms {datetime.utcnow()}", "Diagnosis Style", datetime.utcnow()
            )
            logger.info(f"Created new session: {session_id}")

        response_data = await analyze_symptoms(request.symptoms, current_user)
    
        await conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) "
            "VALUES ($1, $2, $3, $4)",
            session_id, "user", f"Symptoms: {', '.join(request.symptoms)}", datetime.utcnow()
        )
        await conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) "
            "VALUES ($1, $2, $3, $4)",
            session_id, "assistant", f"Diagnosis: {response_data['diagnosis'].diagnosis}\nDescription: {response_data['diagnosis'].description}\nSeverity: {response_data['diagnosis'].severity}\nRecommended Specialty: {response_data['diagnosis'].recommended_speciality}\nConfidence: {response_data['diagnosis'].confidence}", datetime.utcnow()
        )
        return {
            "session_id": session_id,
            "response": response_data["diagnosis"].dict(),
            "suggested_doctors": response_data["suggested_doctors"]
        }
    except Exception as e:
        logger.error(f"Failed to process symptoms: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process symptoms")
    finally:
        await conn.close()

@router.get("/sessions/latest")
async def get_latest_session(current_user: User = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        result = await conn.fetchrow(
            "SELECT id FROM sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
            str(current_user.id)
        )
        if not result:
            raise HTTPException(status_code=404, detail="No session found.")
        return {"session_id": result["id"]}
    except Exception as e:
        logger.error(f"Failed to fetch latest session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest session")
    finally:
        await conn.close()

@router.get("/messages")
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        messages = await conn.fetch(
            "SELECT role, content FROM messages WHERE session_id = $1 ORDER BY created_at ASC",
            session_id
        )
        return [{"role": m["role"], "content": m["content"]} for m in messages]
    except Exception as e:
        logger.error(f"Failed to fetch messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")
    finally:
        await conn.close()

@router.post("/general")
async def general_query_endpoint(
    request: GeneralQueryRequest,
    force_new: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    return await handle_general_query(request, current_user, force_new=force_new)

@router.get("/sessions")
async def get_all_sessions(offset: int = 0, limit: int = 10, current_user: User = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT id, session_name, created_at FROM sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
            str(current_user.id), limit, offset
        )
        return [{"id": r["id"], "name": r["session_name"], "created_at": r["created_at"]} for r in rows]
    except Exception as e:
        logger.error(f"Failed to fetch sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")
    finally:
        await conn.close()

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: User = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        session = await conn.fetchrow("SELECT id FROM sessions WHERE id = $1 AND user_id = $2", session_id, str(current_user.id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")
        
        await conn.execute("DELETE FROM messages WHERE session_id = $1", session_id)
        await conn.execute("DELETE FROM sessions WHERE id = $1", session_id)
        return {"message": "Session deleted"}
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")
    finally:
        await conn.close()

@router.put("/sessions/{session_id}/rename")
async def rename_session(session_id: str, request: dict, current_user: User = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        session = await conn.fetchrow(
            "SELECT id FROM sessions WHERE id = $1 AND user_id = $2",
            session_id,
            str(current_user.id)
        )
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")

        name = request.get("name")
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")

        await conn.execute(
            "UPDATE sessions SET session_name = $1 WHERE id = $2",
            name.strip(),
            session_id
        )
        return {"message": "Session renamed"}
    except Exception as e:
        logger.error(f"Failed to rename session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rename session: {str(e)}")
    finally:
        await conn.close()

@router.get("/tip")
async def get_health_tip_openai():
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": "You are a health coach. Give one short, practical health tip for the general public. Be specific, avoid generalities."
                },
                {
                    "role": "user",
                    "content": "Give me one helpful daily health tip."
                }
            ],
            max_tokens=60
        )
        tip = response.choices[0].message.content.strip()
        return {"tip": tip}
    except Exception as e:
        logger.error(f"Failed to generate health tip: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not generate health tip")