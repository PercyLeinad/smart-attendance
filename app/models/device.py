from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from app.models.database import Base
from datetime import datetime, UTC

class Device(Base):
    __tablename__ = "devices"

    __table_args__ = (
        UniqueConstraint("staff_pf", "fingerprint_hash", name="uq_staff_device"),
    )

    id = Column(Integer, primary_key=True)

    # Link to the user/staff
    staff_pf = Column(String(50), nullable=False, index=True)

    fingerprint_hash = Column(String(255), nullable=False)

    user_agent = Column(Text)
    screen_resolution = Column(String(50))
    timezone = Column(String(50))
    language = Column(String(50))
    ip_address = Column(String(45))

    last_seen = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)