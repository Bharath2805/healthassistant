from google.oauth2 import id_token
from google.auth.transport import requests

def decode_google_token(token: str):
    try:
        # Replace this with your actual Google Client ID
        CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

        # Extract relevant information
        user_id = idinfo["sub"]
        email = idinfo["email"]
        verified = idinfo.get("email_verified", False)

        if not verified:
            raise ValueError("Email not verified by Google")

        return {
            "google_id": user_id,
            "email": email
        }
    except Exception as e:
        raise ValueError(f"Invalid Google token: {str(e)}")
