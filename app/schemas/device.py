from typing import List
from pydantic import BaseModel, field_validator
from datetime import datetime

class DeviceInfo(BaseModel):
    user_agent: str
    screen_resolution: str
    timezone: str
    language: str
    device_id: str

class DeviceRiskReportItem(BaseModel):
    staff_pf: str
    name: str
    device_count: int
    ip_changes: int
    shared_device_flag: int
    last_seen: datetime | None
    risk_score: int


class DeviceRiskReportResponse(BaseModel):
    data: List[DeviceRiskReportItem]