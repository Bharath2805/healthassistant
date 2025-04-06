from pydantic import BaseModel, validator
from datetime import time, datetime

class ReminderCreate(BaseModel):
    medicine: str
    reminder_time: time  # Format: HH:MM:SS
    frequency: str = "daily"

    @validator("frequency")
    def validate_frequency(cls, v):
        valid_frequencies = ["daily", "weekly", "monthly"]
        if v not in valid_frequencies:
            raise ValueError(f"Frequency must be one of {valid_frequencies}")
        return v

class ReminderHistoryResponse(BaseModel):
    id: int
    user_id: str
    reminder_id: int
    sent_at: datetime
    delivery_status: str
