from pydantic import BaseModel, field_validator

class DeviceInfo(BaseModel):
    user_agent: str
    screen_resolution: str
    timezone: str
    language: str