
from pydantic import BaseModel, field_validator,Field
from typing import Optional
from app.schemas.device import DeviceInfo
   
class AttendanceRequest(BaseModel):
    staff_id: str
    token: str
    confirm: Optional[bool] = False
    device_info: Optional[DeviceInfo] = None
    
    @field_validator('staff_id')
    @classmethod
    def force_uppercase(cls, v: str) -> str:
        return v.upper()

