from celery import Celery
from backend.database import get_db_connection
from backend.utils.email import send_email
from backend.utils.sms import send_sms_notification
from backend.services.reminders import log_reminder_history
from datetime import datetime
import asyncio
import logging
import pytz
import os
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "../.env"))  # Adjusted path to reach .env in parent directory

# Configuration from environment variables
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

celery = Celery("reminders", broker="redis://localhost:6379/0")
logger = logging.getLogger(__name__)

def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@celery.task
def check_reminders():
    local_tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(local_tz).strftime("%H:%M")
    logger.info(f"📅 Checking reminders at {now}")

    reminders = run_async(get_due_reminders(now))

    for r in reminders:
        try:
            user = run_async(get_user_email_and_phone(r["user_id"]))
            if user:
                status = []
                
                subject = f"Health Reminder: Take your {r['medicine']} at {r['reminder_time']}"
                body = (
                    f"Hello,\n\n"
                    f"This is your scheduled health reminder from Health Assistant.\n\n"
                    f"💊 Medicine: {r['medicine']}\n"
                    f"⏰ Time: {r['reminder_time']}\n\n"
                    f"For more details, visit {BASE_URL}/health-assistant\n\n"
                    "Stay healthy and take care!\n"
                    "— Your Health Assistant Team\n\n"
                    "You received this reminder because you opted in via our app."
                )

                if user["preferred_notification"] in ("email", "both"):
                    send_email(
                        to_email=user["email"],
                        subject=subject,
                        body=body
                    )
                    status.append("email")

                if user["preferred_notification"] in ("sms", "both") and user.get("phone"):
                    send_sms_notification(
                        to_number=user["phone"],
                        body=f"💊 Reminder: Take {r['medicine']} at {r['reminder_time']}"
                    )
                    status.append("sms")

                final_status = "-".join(status) + "-sent" if status else "no-delivery"
                run_async(log_reminder_history(reminder_id=r["id"], user_id=r["user_id"], status=final_status))
            else:
                run_async(log_reminder_history(reminder_id=r["id"], user_id=r["user_id"], status="user-not-found"))
        except Exception as e:
            logger.error(f"❌ Failed to send reminder: {e}")
            run_async(log_reminder_history(reminder_id=r["id"], user_id=r["user_id"], status="failed"))

# 🔍 Get reminders due now
async def get_due_reminders(current_time: str):
    conn = await get_db_connection()
    try:
        return await conn.fetch(
            "SELECT * FROM reminders WHERE reminder_time::text LIKE $1 AND status = 'active'",
            f"{current_time}%"
        )
    finally:
        await conn.close()

# 👤 Fetch email, phone, preference
async def get_user_email_and_phone(user_id: str):
    conn = await get_db_connection()
    try:
        return await conn.fetchrow(
            "SELECT email, phone, preferred_notification FROM users WHERE id = $1",
            user_id
        )
    finally:
        await conn.close()

# 🔁 Schedule task every minute
celery.conf.beat_schedule = {
    "check-reminders-every-minute": {
        "task": "backend.tasks.tasks.check_reminders",
        "schedule": 60.0,
    },
}