from pydantic import BaseModel
from datetime import datetime

class ReminderHistory(BaseModel):
    reminder_id: int
    user_id: str
    sent_at: datetime = None
    delivery_status: str = "pending"
