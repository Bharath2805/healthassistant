# backend/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
from jose import jwt
import httpx
import os
import uuid
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from backend.auth.auth import signup, login, get_current_user
from backend.auth.schemas import (
    UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, User, PasswordUpdateRequest
)
from backend.database import get_db_connection
from backend.auth.utils.tokens import (
    create_email_token, verify_email_token, create_access_token,
    verify_refresh_token, create_refresh_token
)
from backend.utils.email import send_email
from backend.auth.utils.hash import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

# Configuration from environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = f"{BACKEND_URL}/auth/google-callback"

# -------------------- MODELS --------------------
class PhoneUpdateRequest(BaseModel):
    phone: str

class NotificationPreferenceRequest(BaseModel):
    method: str  # 'email', 'sms', or 'both'

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class SetPasswordRequest(BaseModel):
    new_password: str

class GoogleLoginRequest(BaseModel):
    token: str  # Google ID token from frontend

# -------------------- SIGNUP + LOGIN --------------------
@router.post("/signup")
async def signup_endpoint(user: UserCreate):
    logger.info(f"Signup attempt for email: {user.email}")
    return await signup(user)

@router.post("/login")
async def login_endpoint(user: UserLogin, request: Request):
    return await login(user, request)

# -------------------- GOOGLE LOGIN (REDIRECT FLOW) --------------------
@router.get("/google-login")
async def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth configuration missing")
        raise HTTPException(status_code=500, detail="Google OAuth configuration missing")
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid%20email"
        f"&redirect_uri={REDIRECT_URI}"
    )
    logger.info("Redirecting to Google OAuth login")
    return RedirectResponse(google_auth_url)

@router.get("/google-callback")
async def google_callback(code: str):
    logger.info("Handling Google OAuth callback")
    async with httpx.AsyncClient() as client:
        token_response = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        })

        if token_response.status_code != 200:
            logger.error(f"Failed to get access token from Google: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get access token")

        tokens = token_response.json()
        id_token_str = tokens["id_token"]

        payload = jwt.get_unverified_claims(id_token_str)
        email = payload.get("email")

        if not email:
            logger.error("Email not found in Google ID token")
            raise HTTPException(status_code=400, detail="Email not found in token")

        conn = await get_db_connection()
        try:
            user = await conn.fetchrow("SELECT id, email, role FROM users WHERE email = $1", email)
            if not user:
                user_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO users (id, email, password, role, is_verified, auth_provider) 
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id, email, "", "user", True, "google"
                )
                role = "user"
            else:
                user_id = user["id"]
                role = user["role"]

            access_token = create_access_token(user_id, role)
            refresh_token = create_refresh_token(user_id)

            expires_at = datetime.utcnow() + timedelta(days=7)
            await conn.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES ($1, $2, $3)",
                user_id, refresh_token, expires_at
            )

            logger.info(f"Google login successful for email: {email}")
            frontend_redirect_url = (
                f"{FRONTEND_URL}/google-auth-success"
                f"?access_token={access_token}&refresh_token={refresh_token}"
            )
            return RedirectResponse(url=frontend_redirect_url)
        finally:
            await conn.close()

# -------------------- GOOGLE LOGIN (TOKEN-BASED FLOW) --------------------
@router.post("/google-login-token")
async def google_login_token(request: GoogleLoginRequest):
    try:
        id_info = id_token.verify_oauth2_token(
            request.token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = id_info["email"]

        conn = await get_db_connection()
        try:
            user = await conn.fetchrow("SELECT id, email, role FROM users WHERE email = $1", email)
            if not user:
                user_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO users (id, email, password, role, auth_provider, is_verified)
                    VALUES ($1, $2, NULL, 'user', 'google', TRUE)
                    """,
                    user_id, email
                )
                role = "user"
            else:
                user_id = user["id"]
                role = user["role"]

            access_token = create_access_token(user_id, role)
            refresh_token = create_refresh_token(user_id)

            expires_at = datetime.utcnow() + timedelta(days=7)
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token, expires_at)
                VALUES ($1, $2, $3)
                """,
                user_id, refresh_token, expires_at
            )

            logger.info(f"Google token login successful for email: {email}")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "message": "Google login successful"
            }
        finally:
            await conn.close()
    except ValueError as e:
        logger.error(f"Google token validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Google token")

# -------------------- SET PASSWORD FOR GOOGLE USERS --------------------
@router.post("/set-password")
async def set_password(
    request: SetPasswordRequest,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Password set requested for user_id: {current_user.id}")
    conn = await get_db_connection()
    try:
        user = await conn.fetchrow("SELECT auth_provider, password FROM users WHERE id = $1", current_user.id)
        if not user:
            logger.error(f"User not found for id: {current_user.id}")
            raise HTTPException(status_code=404, detail="User not found")

        if user["auth_provider"] != "google":
            logger.warning(f"User {current_user.id} is not a Google user")
            raise HTTPException(status_code=400, detail="Password can only be set for Google accounts")

        if user["password"]:
            logger.warning(f"User {current_user.id} already has a password set")
            raise HTTPException(status_code=403, detail="Password already set")

        hashed_pw = hash_password(request.new_password)
        await conn.execute(
            "UPDATE users SET password = $1 WHERE id = $2", hashed_pw, current_user.id
        )
        logger.info(f"Password set successfully for user_id: {current_user.id}")
        return {"message": "Password set successfully"}
    finally:
        await conn.close()

# -------------------- EMAIL VERIFICATION --------------------
@router.get("/verify-email")
async def verify_email(token: str = Query(...)):
    try:
        user_id = verify_email_token(token)
        conn = await get_db_connection()
        try:
            user = await conn.fetchrow("SELECT id, email FROM users WHERE id = $1", user_id)
            if not user:
                logger.error(f"User not found for id: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            await conn.execute("UPDATE users SET is_verified = TRUE WHERE id = $1", user_id)
            logger.info(f"Email verified for user_id: {user_id}")
            return {"message": "Email verified successfully!"}
        finally:
            await conn.close()
    except ValueError as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# -------------------- RESEND VERIFICATION --------------------
@router.post("/resend-verification")
async def resend_verification(request: ForgotPasswordRequest):
    logger.info(f"Resend verification requested for email: {request.email}")
    conn = await get_db_connection()
    try:
        user = await conn.fetchrow("SELECT id, is_verified FROM users WHERE email = $1", request.email)
        if not user:
            logger.error(f"Email not found: {request.email}")
            raise HTTPException(status_code=404, detail="Email not found")
        if user["is_verified"]:
            logger.info(f"Email already verified for: {request.email}")
            return {"message": "Email is already verified"}

        token = create_email_token(user["id"])
        link = f"{BACKEND_URL}/auth/verify-email?token={token}"
        try:
            send_email(
                to_email=request.email,
                subject="Verify your email",
                body=f"Click here to verify your email: {link}"
            )
            logger.info(f"Verification email resent to: {request.email}")
        except Exception as e:
            logger.error(f"Failed to resend verification email to {request.email}: {str(e)}")
        return {"message": "Verification email resent successfully"}
    finally:
        await conn.close()

# -------------------- FORGOT PASSWORD --------------------
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    logger.info(f"Forgot password requested for email: {request.email}")
    conn = await get_db_connection()
    try:
        user = await conn.fetchrow("SELECT id, email FROM users WHERE email = $1", request.email)
        if not user:
            logger.error(f"Email not found: {request.email}")
            raise HTTPException(status_code=404, detail="Email not found")

        token = create_email_token(user["id"])
        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
        try:
            send_email(
                to_email=request.email,
                subject="Reset your password",
                body=f"Click here to reset your password: {reset_link}"
            )
            logger.info(f"Password reset link sent to: {request.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {request.email}: {str(e)}")
        return {"message": "Password reset link sent to your email"}
    finally:
        await conn.close()

# -------------------- RESET PASSWORD --------------------
@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    logger.info("Password reset requested")
    try:
        user_id = verify_email_token(request.token)
    except ValueError as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    conn = await get_db_connection()
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE id = $1", user_id)
        if not user:
            logger.error(f"User not found for id: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        hashed_pw = hash_password(request.new_password)
        await conn.execute("UPDATE users SET password = $1 WHERE id = $2", hashed_pw, user_id)
        logger.info(f"Password reset successful for user_id: {user_id}")
        return {"message": "Password reset successful"}
    finally:
        await conn.close()

# -------------------- UPDATE PASSWORD --------------------
@router.put("/update-password")
async def update_password(
    request: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Password update requested for user_id: {current_user.id}")
    if not current_user.id:
        logger.error("Unauthorized attempt to update password")
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = await get_db_connection()
    try:
        user = await conn.fetchrow("SELECT password FROM users WHERE id = $1", current_user.id)
        if not user:
            logger.error(f"User not found for id: {current_user.id}")
            raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(request.old_password, user["password"]):
            logger.warning(f"Old password incorrect for user_id: {current_user.id}")
            raise HTTPException(status_code=403, detail="Old password is incorrect")

        hashed = hash_password(request.new_password)
        await conn.execute("UPDATE users SET password = $1 WHERE id = $2", hashed, current_user.id)
        logger.info(f"Password updated successfully for user_id: {current_user.id}")
        return {"message": "Password updated successfully"}
    finally:
        await conn.close()

# -------------------- REFRESH TOKEN --------------------
@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    logger.info("Refresh token requested")
    try:
        user_id = verify_refresh_token(request.refresh_token)
        conn = await get_db_connection()
        try:
            record = await conn.fetchrow(
                """
                SELECT * FROM refresh_tokens 
                WHERE token = $1 AND revoked = FALSE AND expires_at > NOW()
                """,
                request.refresh_token
            )
            if not record:
                logger.error(f"Invalid or expired refresh token for user_id: {user_id}")
                raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

            user = await conn.fetchrow("SELECT id, role FROM users WHERE id = $1", user_id)
            if not user:
                logger.error(f"User not found for id: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")

            new_access_token = create_access_token(user["id"], user["role"])
            new_refresh_token = create_refresh_token(user["id"])
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            await conn.execute(
                "UPDATE refresh_tokens SET revoked = TRUE WHERE token = $1",
                request.refresh_token
            )
            await conn.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES ($1, $2, $3)",
                user["id"], new_refresh_token, expires_at
            )

            logger.info(f"Access token refreshed for user_id: {user_id}")
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
        finally:
            await conn.close()
    except ValueError as e:
        logger.error(f"Refresh token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

# -------------------- REFRESH TOKEN (NEW ENDPOINT) --------------------
@router.post("/refresh-token")
async def refresh_token_endpoint(request: RefreshTokenRequest):
    logger.info("Refresh token requested via /refresh-token")
    try:
        user_id = verify_refresh_token(request.refresh_token)
        conn = await get_db_connection()
        try:
            record = await conn.fetchrow(
                """
                SELECT * FROM refresh_tokens 
                WHERE token = $1 AND revoked = FALSE AND expires_at > NOW()
                """,
                request.refresh_token
            )
            if not record:
                logger.error(f"Invalid or expired refresh token for user_id: {user_id}")
                raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

            user = await conn.fetchrow("SELECT id, role FROM users WHERE id = $1", user_id)
            if not user:
                logger.error(f"User not found for id: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")

            new_access_token = create_access_token(user["id"], user["role"])
            new_refresh_token = create_refresh_token(user["id"])
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            await conn.execute(
                "UPDATE refresh_tokens SET revoked = TRUE WHERE token = $1",
                request.refresh_token
            )
            await conn.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES ($1, $2, $3)",
                user["id"], new_refresh_token, expires_at
            )

            logger.info(f"Access token refreshed for user_id: {user_id} via /refresh-token")
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
        finally:
            await conn.close()
    except ValueError as e:
        logger.error(f"Refresh token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

# -------------------- LOGOUT --------------------
@router.post("/logout")
async def logout(request: RefreshTokenRequest):
    logger.info("Logout requested")
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE token = $1",
            request.refresh_token
        )
        if result == "UPDATE 0":
            logger.warning(f"Refresh token not found or already revoked: {request.refresh_token}")
            raise HTTPException(status_code=400, detail="Refresh token not found or already revoked")
        
        logger.info("Logout successful")
        return {"message": "Logged out successfully"}
    finally:
        await conn.close()

# -------------------- PROFILE SETTINGS --------------------
@router.put("/update-phone")
async def update_phone(request: PhoneUpdateRequest, current_user: User = Depends(get_current_user)):
    if not current_user.id:
        logger.error("Unauthorized attempt to update phone")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"Updating phone for user_id: {current_user.id}")
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET phone = $1 WHERE id = $2",
            request.phone, current_user.id
        )
        return {"message": "Phone number updated successfully"}
    finally:
        await conn.close()

@router.put("/set-notification-method")
async def set_notification_method(request: NotificationPreferenceRequest, current_user: User = Depends(get_current_user)):
    if request.method not in ("email", "sms", "both"):
        logger.error(f"Invalid notification method: {request.method}")
        raise HTTPException(status_code=400, detail="Invalid method. Choose from 'email', 'sms', or 'both'")

    if not current_user.id:
        logger.error("Unauthorized attempt to set notification method")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"Setting notification method to '{request.method}' for user_id: {current_user.id}")
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET preferred_notification = $1 WHERE id = $2",
            request.method, current_user.id
        )
        return {"message": f"Notification method set to '{request.method}'"}
    finally:
        await conn.close()