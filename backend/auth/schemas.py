# backend/auth/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

# ----------- Public User Object -----------
class User(BaseModel):
    id: Optional[UUID]  # Updated to Optional[UUID] for stricter validation
    email: EmailStr
    role: str = "user"

# ----------- Auth Input -----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ----------- JWT Token Response -----------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ----------- Email Verification + Password Reset -----------
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

# ----------- Profile Update (Optional) -----------
class UserProfileUpdate(BaseModel):
    phone: Optional[str]
    preferred_notification: Optional[str]  # "email", "sms", "both"

# ----------- Password Update (with old password) -----------
class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)