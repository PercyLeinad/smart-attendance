from sqlalchemy import text
from sqlalchemy.engine import Connection

def get_user(connection: Connection, identifier: str):
    """Fetches the primary or personal email for a given PF number."""
    query = text("""
        SELECT email, personal_email 
        FROM employees 
        WHERE (pf = :identifier OR id_number = :identifier) AND status = 'Active'
        LIMIT 1
    """)
    
    return connection.execute(query, {"identifier": identifier}).fetchone()