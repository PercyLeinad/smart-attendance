from sqlalchemy import text
from sqlalchemy.engine import Connection

def get_user_email_by_pf(connection: Connection, identifier: str) -> str:
    """Fetches the primary or personal email for a given PF number."""
    query = text("""
        SELECT email, personal_email 
        FROM employees 
        WHERE (pf = :identifier OR id_number = :identifier) AND status = 'Active'
        LIMIT 1
    """)
    
    result = connection.execute(query, {"identifier": identifier}).fetchone()
    
    if not result:
        raise ValueError("User not found or inactive.")
    
    # Prioritize professional email, fallback to personal_email
    email = result.email if result.email else result.personal_email

    return email