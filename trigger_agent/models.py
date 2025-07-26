from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class SupportEvent(BaseModel):
    id: int
    customer_id: int
    type: str  # e.g., "login", "call", "inactivity"
    timestamp: datetime


class TriggerType(str, Enum):
    MULTIPLE_CALLS = "multiple_calls"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    USAGE_NEARING_CAP = "usage_nearing_cap"
    INACTIVITY = "inactivity_reengagement"

class Trigger(BaseModel):
    customer_id: int
    trigger_type: TriggerType 
    detected_at: datetime
