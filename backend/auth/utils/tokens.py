# backend/auth/utils/tokens.py
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from uuid import UUID


load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
REFRESH_SECRET = os.getenv("REFRESH_SECRET", "default-refresh-secret")
ALGORITHM = "HS256"

def create_email_token(user_id):
    payload = {
        "sub": str(user_id),  # ✅ Convert UUID to string
        "type": "email-verification",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
          

def verify_email_token(token: str) -> str:
    """
    Verify an email verification or password reset token and return the user_id.
    Raises ValueError if the token is invalid, expired, or not of the correct type.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email-verification":
            raise ValueError("Invalid token type: expected 'email-verification'")
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def create_access_token(user_id: UUID, role: str):
    payload = {
        "sub": str(user_id),  # 🔥 Convert UUID to string
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify an access token, returning its payload.
    Raises ValueError if the token is invalid or expired.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Access token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid access token")

def create_refresh_token(user_id: str, expires_in_minutes: int = 1440) -> str:
    """
    Create a JWT refresh token for refreshing access tokens.
    """
    payload = {
        "sub": str(user_id),  # ✅ Fix here
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    }
    return jwt.encode(payload, REFRESH_SECRET, algorithm=ALGORITHM)


def verify_refresh_token(token: str) -> str:
    """
    Verify a refresh token and return the user_id.
    Raises ValueError if the token is invalid, expired, or not of the correct type.
    """
    try:
        payload = jwt.decode(token, REFRESH_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type: expected 'refresh'")
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise ValueError("Refresh token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid refresh token")