import secrets
import datetime
from typing import Optional
from sqlalchemy import text, Connection

def create_user_session(
    conn: Connection, 
    username: str, 
    ip_address: Optional[str] = None, 
    user_agent: Optional[str] = None
) -> str:
    """Generates a secure token, inserts the session row, and returns the token string."""
    token = secrets.token_urlsafe(32)
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) # Keep it naive for standard MySQL DATETIME
    
    query = text("""
        INSERT INTO sessions (session_id, username, last_activity, created_at, ip_address, user_agent)
        VALUES (:session_id, :username, :last_activity, :created_at, :ip_address, :user_agent)
    """)
    
    conn.execute(query, {
        "session_id": token,
        "username": username,
        "last_activity": now,
        "created_at": now,
        "ip_address": ip_address,
        "user_agent": user_agent
    })
    return token

def get_session_by_id(conn: Connection, session_id: str) -> Optional[dict]:
    """Retrieves the session record as a dictionary mapping."""
    query = text("""
        SELECT session_id, username, last_activity, created_at, ip_address, user_agent 
        FROM sessions 
        WHERE session_id = :session_id
    """)
    result = conn.execute(query, {"session_id": session_id}).mappings().first()
    return dict(result) if result else None

def update_session_activity(conn: Connection, session_id: str) -> None:
    """Pushes the sliding window timeout forward by updating the last_activity column."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    query = text("""
        UPDATE sessions 
        SET last_activity = :now 
        WHERE session_id = :session_id
    """)
    conn.execute(query, {"now": now, "session_id": session_id})

def delete_user_session(conn: Connection, session_id: str) -> None:
    """Deletes the session row completely from the database."""
    query = text("DELETE FROM sessions WHERE session_id = :session_id")
    conn.execute(query, {"session_id": session_id})