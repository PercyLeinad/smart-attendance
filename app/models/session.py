import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base

class SessionModel(Base):
    __tablename__ = "sessions"

    # Mapped[...] tells the IDE the runtime type, 
    # while mapped_column(...) handles the database schema definition.
    session_id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    last_activity: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc), 
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc), 
        nullable=False
    )
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc), 
        nullable=False
    )
    
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    def is_expired(self, timeout_seconds: int) -> bool:
        """Helper to quickly check if the sliding window timeout has passed."""
        expiry_time = self.last_activity + datetime.timedelta(seconds=timeout_seconds)
        return bool(datetime.datetime.now(datetime.timezone.utc) > expiry_time)