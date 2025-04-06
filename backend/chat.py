from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.auth import User, get_current_user
 
from backend.database import get_db_connection
import uuid
from datetime import datetime

# Initialize the router for chat-related endpoints
router = APIRouter(prefix="/chat", tags=["Chat"])

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    id: str
    user_id: str
    message: str
    response: str
    timestamp: datetime

class ChatSession(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    messages: List[ChatResponse] = []

# Helper function to simulate a chatbot response (replace with your actual logic)
def generate_bot_response(message: str) -> str:
    # This is a placeholder. You can integrate an actual AI model or logic here.
    return f"Bot response to: {message}"

# Endpoint to create a new chat session
@router.post("/session", response_model=ChatSession)
async def create_session(current_user: User = Depends(get_current_user)):
    if not current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO chat_sessions (session_id, user_id, created_at) VALUES ($1, $2, $3)",
            session_id, current_user.id, created_at
        )
        return ChatSession(session_id=session_id, user_id=current_user.id, created_at=created_at)
    finally:
        await conn.close()

# Endpoint to get all chat sessions for the current user
@router.get("/sessions", response_model=List[ChatSession])
async def get_sessions(current_user: User = Depends(get_current_user)):
    if not current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = await get_db_connection()
    try:
        # Fetch all sessions for the user
        sessions = await conn.fetch(
            "SELECT session_id, user_id, created_at FROM chat_sessions WHERE user_id = $1",
            current_user.id
        )
        result = []
        for session in sessions:
            # Fetch messages for each session
            messages = await conn.fetch(
                "SELECT id, user_id, message, response, timestamp FROM chat_messages WHERE session_id = $1",
                session["session_id"]
            )
            message_list = [
                ChatResponse(
                    id=msg["id"],
                    user_id=msg["user_id"],
                    message=msg["message"],
                    response=msg["response"],
                    timestamp=msg["timestamp"]
                )
                for msg in messages
            ]
            result.append(
                ChatSession(
                    session_id=session["session_id"],
                    user_id=session["user_id"],
                    created_at=session["created_at"],
                    messages=message_list
                )
            )
        return result
    finally:
        await conn.close()

# Endpoint to send a message in a chat session
@router.post("/{session_id}/message", response_model=ChatResponse)
async def chat(session_id: str, request: ChatRequest, current_user: User = Depends(get_current_user)):
    if not current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Verify the session exists and belongs to the user
    conn = await get_db_connection()
    try:
        session = await conn.fetchrow(
            "SELECT session_id, user_id FROM chat_sessions WHERE session_id = $1 AND user_id = $2",
            session_id, current_user.id
        )
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found or not authorized")

        # Generate a bot response (replace with your actual logic)
        bot_response = generate_bot_response(request.message)

        # Save the message and response to the database
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        await conn.execute(
            "INSERT INTO chat_messages (id, session_id, user_id, message, response, timestamp) "
            "VALUES ($1, $2, $3, $4, $5, $6)",
            message_id, session_id, current_user.id, request.message, bot_response, timestamp
        )

        return ChatResponse(
            id=message_id,
            user_id=current_user.id,
            message=request.message,
            response=bot_response,
            timestamp=timestamp
        )
    finally:
        await conn.close()