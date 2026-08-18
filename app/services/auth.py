from sqlalchemy import text
from sqlalchemy.engine import Connection

def get_dashboard_stats(conn: Connection):
    return conn.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM employees) AS total_employees,
            (SELECT COUNT(*) FROM attendance_logs WHERE date_only = CURDATE()) AS today_attendance,
            (SELECT COUNT(*) FROM employees WHERE pf NOT LIKE 'CA%') AS permanent,
            (SELECT COUNT(*) FROM employees WHERE pf LIKE 'CA%') AS casuals
    """)).mappings().one()

def list_all_admins(conn: Connection):
    return conn.execute(
        text("SELECT username, created_at, email FROM masters ORDER BY created_at ASC")
    ).mappings().all()

def add_new_admin(conn: Connection, username: str, email: str, hashed_password: str):
    conn.execute(
        text("INSERT INTO masters (username, email, password) VALUES (:u, :e, :p)"),
        {"u": username, "e": email, "p": hashed_password}
    )

def delete_admin_by_username(conn: Connection, username: str):
    conn.execute(
        text("DELETE FROM masters WHERE username = :u"),
        {"u": username}
    )

def update_admin_password(conn: Connection, username: str, hashed_password: str):
    conn.execute(
        text("UPDATE masters SET password = :p WHERE username = :u"),
        {"p": hashed_password, "u": username}
    )

def get_admin_password(conn, username: str):
    result = conn.execute(
        text("SELECT password FROM masters WHERE username = :username"),
        {"username": username}
    )
    return result.mappings().one_or_none()


def get_all_admins_basic(conn):
    result = conn.execute(
        text("SELECT username, created_at FROM masters")
    )
    return result.fetchall()

def get_admin_by_username(conn, username: str):
    result = conn.execute(
        text("SELECT email FROM masters WHERE username = :username"),
        {"username": username}
    )
    return result.mappings().one_or_none()


from datetime import datetime, timezone

def create_session(
    conn,
    session_id: str,
    username: str,
    ip_address: str | None,
    user_agent: str | None
):
    """
    Create a new session audit record.
    """

    created_at = datetime.now(timezone.utc)

    conn.exec_driver_sql(
        """
        INSERT INTO sessions (
            session_id,
            username,
            created_at,
            ip_address,
            user_agent
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            session_id,
            username,
            created_at,
            ip_address,
            user_agent
        )
    )

def close_session(
    conn,
    session_id: str,
    logout_reason: str
):
    """
    Mark a session as closed in the audit table.
    """

    logout_at = datetime.now(timezone.utc)

    conn.exec_driver_sql(
        """
        UPDATE sessions
        SET
            logout_at = %s,
            logout_reason = %s
        WHERE session_id = %s
          AND logout_at IS NULL
        """,
        (
            logout_at,
            logout_reason,
            session_id
        )
    )