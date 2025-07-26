from pydantic import BaseModel
from datetime import datetime

class SupportEvent(BaseModel):
    id: int
    customer_id: int
    type: str  # e.g., "login", "call", "inactivity"
    timestamp: datetime

class Trigger(BaseModel):
    customer_id: int
    trigger_type: str  # e.g., "multiple_calls"
    detected_at: datetime