
from pydantic import BaseModel, field_validator,Field


class AttendanceRequest(BaseModel):
    staff_id: str = Field(max_length=10, description="The staff ID or PF number")
    token: str
    
    @field_validator('staff_id')
    @classmethod
    def force_uppercase(cls, v: str) -> str:
        return v.upper()