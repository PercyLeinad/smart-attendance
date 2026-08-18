from sqlalchemy import text
from app.core.database import engine

# Run every 10–15 minutes
def cleanup_expired_db_sessions(engine):
    query = text("""
    UPDATE sessions
    SET logout_at = DATE_ADD(created_at, INTERVAL 30 MINUTE),
        logout_reason = 'expire'
    WHERE logout_reason IS NULL 
      AND TIMESTAMPDIFF(MINUTE, created_at, UTC_TIMESTAMP()) >= 30 
    """)

    with engine.begin() as conn:
        conn.execute(query)

if __name__ == "__main__":
    cleanup_expired_db_sessions(engine)