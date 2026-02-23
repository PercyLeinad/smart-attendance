
from pydantic import BaseModel, field_validator


class AttendanceRequest(BaseModel):
    staff_id: str
    token: str
    
    @field_validator('staff_id')
    @classmethod
    def force_uppercase(cls, v: str) -> str:
        return v.upper()