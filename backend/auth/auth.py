from fastapi import Depends, HTTPException, APIRouter, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import jwt
from jwt import PyJWTError as JWTError
from datetime import datetime, timedelta
import logging

from backend.database import get_db_connection
from backend.auth.schemas import UserCreate, User, UserLogin
from backend.auth.utils.hash import hash_password, verify_password
from backend.auth.utils.tokens import (
    create_email_token,
    create_access_token,
    create_refresh_token,
    decode_access_token
)
from backend.utils.email import send_email

logger = logging.getLogger(__name__)
router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # ✅ ADDED
security = HTTPBearer()
oauth2_scheme = HTTPBearer()

# ----------- MODELS -----------
class User(BaseModel):
    id: Optional[str]
    email: str
    role: str = "user"

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class PhoneUpdateRequest(BaseModel):
    phone: str

class PreferenceUpdateRequest(BaseModel):
    preference: str  # "email", "sms", or "both"

# ----------- USER DEPENDENCY -----------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        credentials: str = token.credentials
        payload = jwt.decode(credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        conn = await get_db_connection()
        try:
            user = await conn.fetchrow("SELECT id, email, role FROM users WHERE id = $1", uuid.UUID(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            return User(
                id=str(user["id"]),
                email=user["email"],
                role=user["role"]
            )
        finally:
            await conn.close()
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

# ----------- AUTH HANDLERS -----------
async def signup(user: UserCreate) -> dict:
    logger.info(f"Signup attempt for email: {user.email}")
    conn = await get_db_connection()
    try:
        existing_user = await conn.fetchrow("SELECT email FROM users WHERE email = $1", user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = str(uuid.uuid4())
        hashed_pwd = hash_password(user.password)

        await conn.execute(
            "INSERT INTO users (id, email, password, role, is_verified) VALUES ($1, $2, $3, $4, $5)",
            user_id, user.email, hashed_pwd, "user", False
        )

        verification_token = create_email_token(user_id)
        verification_link = f"{BASE_URL}/auth/verify-email?token={verification_token}"  # ✅ FIXED

        try:
            send_email(
                to_email=user.email,
                subject="Verify your email",
                body=f"Please verify your email by clicking this link: {verification_link}"
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")

        access_token = create_access_token(user_id, "user")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Signup successful, please verify your email"
        }
    finally:
        await conn.close()

@router.post("/auth/login")
async def login(user: UserLogin, request: Request) -> dict:
    conn = await get_db_connection()
    try:
        db_user = await conn.fetchrow("SELECT id, email, password, role, is_verified FROM users WHERE email = $1", user.email)
        if not db_user or not verify_password(user.password, db_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not db_user["is_verified"]:
            raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

        access_token = create_access_token(db_user["id"], db_user["role"])
        refresh_token = create_refresh_token(db_user["id"])
        expires_at = datetime.utcnow() + timedelta(days=7)

        await conn.execute(
            "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES ($1, $2, $3)",
            db_user["id"], refresh_token, expires_at
        )

        # 📬 Send login alert email
        try:
            user_agent = request.headers.get("user-agent")
            ip_address = request.client.host
            send_email(
                to_email=db_user["email"],
                subject="🔐 New Login Alert - Health Assistant",
                body=f"""Hi,

A new login was detected on your account.

📅 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
🌐 IP: {ip_address}
🖥️ Device: {user_agent}

If this wasn't you, please reset your password immediately.

Stay safe,
Your Health Assistant Team"""
            )
        except Exception as e:
            logger.warning(f"Login alert email failed: {str(e)}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    finally:
        await conn.close()

# ----------- PROFILE UPDATES -----------
@router.put("/user/phone")
async def update_phone(data: PhoneUpdateRequest, current_user: User = Depends(get_current_user)):
    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE users SET phone = $1 WHERE id = $2", data.phone, current_user.id)
        return {"message": "Phone number updated"}
    finally:
        await conn.close()

@router.put("/user/preference")
async def update_preference(data: PreferenceUpdateRequest, current_user: User = Depends(get_current_user)):
    if data.preference not in ["email", "sms", "both"]:
        raise HTTPException(status_code=400, detail="Invalid preference. Use 'email', 'sms', or 'both'.")

    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE users SET preference = $1 WHERE id = $2", data.preference, current_user.id)
        return {"message": f"Notification preference updated to '{data.preference}'"}
    finally:
        await conn.close()
