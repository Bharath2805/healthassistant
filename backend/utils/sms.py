from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

def send_sms_notification(to_number: str, body: str):
    try:
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            body=body,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=to_number
        )
        print(f"SMS sent to {to_number}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")
