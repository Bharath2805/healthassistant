from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.auth.schemas import User
from backend.database import get_db_connection
from backend.auth.utils.tokens import decode_access_token  # ✅ Correct path now

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    role = payload.get("role", "user")

    conn = await get_db_connection()
    try:
        user = await conn.fetchrow("SELECT id, email, role FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return User(id=user["id"], email=user["email"], role=user["role"])
    finally:
        await conn.close()
