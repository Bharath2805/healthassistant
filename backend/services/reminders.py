from fastapi import HTTPException
from backend.database import get_db_connection
from backend.auth import User
from backend.models.reminders import ReminderCreate
import logging

logger = logging.getLogger(__name__)

# Existing: Create Reminder
async def create_reminder(reminder: ReminderCreate, user: User):
    conn = await get_db_connection()
    try:
        logger.info(f"Running query: INSERT INTO reminders with values: {user.id}, {reminder.medicine}, {reminder.reminder_time}, {reminder.frequency}")
        result = await conn.fetchrow(
            "INSERT INTO reminders (user_id, medicine, reminder_time, frequency) VALUES ($1, $2, $3, $4) RETURNING id",
            user.id, reminder.medicine, reminder.reminder_time, reminder.frequency
        )
        return {"message": "Reminder set successfully", "reminder_id": result["id"]}
    except Exception as e:
        logger.error(f"Failed to create reminder: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set reminder")
    finally:
        await conn.close()

# ✅ GET reminders for current user
async def get_reminders(user: User):
    conn = await get_db_connection()
    try:
        reminders = await conn.fetch(
            "SELECT id, medicine, reminder_time, frequency, status, created_at FROM reminders WHERE user_id = $1 ORDER BY created_at DESC",
            user.id
        )
        return [dict(r) for r in reminders]
    finally:
        await conn.close()

# ✅ DELETE a reminder
async def delete_reminder(reminder_id: int, user: User):
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "DELETE FROM reminders WHERE id = $1 AND user_id = $2",
            reminder_id, user.id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Reminder not found or not yours")
        return {"message": f"Reminder {reminder_id} deleted successfully"}
    finally:
        await conn.close()
        
        
        
async def get_reminder_history(user: User):
    conn = await get_db_connection()
    try:
        records = await conn.fetch(
            "SELECT * FROM reminder_history WHERE user_id = $1 ORDER BY sent_at DESC",
            user.id
        )
        return [dict(r) for r in records]
    finally:
        await conn.close()





async def log_reminder_history(reminder_id: int, user_id: str, status: str = "sent"):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO reminder_history (reminder_id, user_id, delivery_status) VALUES ($1, $2, $3)",
            reminder_id, user_id, status
        )
    except Exception as e:
        logger.error(f"Failed to log reminder history: {str(e)}")
    finally:
        await conn.close()
        


