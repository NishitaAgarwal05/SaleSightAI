from pydantic import BaseModel
from datetime import datetime

class PlanChange(BaseModel):
    customer_id: int
    plan_id: str
    timestamp: datetime

class UsageUpdate(BaseModel):
    customer_id: int
    usage_hours: float
    timestamp: datetime

class DeviceEvent(BaseModel):
    customer_id: int
    device_type: str
    status: str
    timestamp: datetime
