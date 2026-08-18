from sqlalchemy import text
from app.core.database import engine
import datetime

# Run every 10–15 minutes
def cleanup_expired_db_sessions(engine):
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    query = text("""
    UPDATE sessions
    SET logout_at = DATE_ADD(created_at, INTERVAL 30 MINUTE),
        logout_reason = 'expire'
    WHERE logout_reason IS NULL 
      AND TIMESTAMPDIFF(MINUTE, created_at, UTC_TIMESTAMP()) >= 30 
    """)

    with engine.begin() as conn:
        result = conn.execute(query)
        # Flush stdout immediately so output writes to the cron log file without buffering
        print(f"[{now_utc}] Session cleanup ran. Updated {result.rowcount} row(s).", flush=True)

if __name__ == "__main__":
    cleanup_expired_db_sessions(engine)