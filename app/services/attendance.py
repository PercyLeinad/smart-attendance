from sqlalchemy import text
from sqlalchemy.engine import Connection
from datetime import date, datetime

def get_employee_by_id_or_pf(conn: Connection, sid: str):
    """Resolves a staff member's real name and PF from either PF or ID number."""
    return conn.execute(
        text("""
            SELECT name, pf 
            FROM employees 
            WHERE id_number = :sid OR pf = :sid
        """),
        {"sid": sid}
    ).mappings().one_or_none()

def get_attendance_record(conn: Connection, pf: str, today: date):
    """Retrieves the attendance record for a specific staff member today."""
    return conn.execute(
        text("""
            SELECT arrival_time, checkout_time
            FROM attendance_logs
            WHERE pf = :pf
            AND date_only = :today
            LIMIT 1
        """),
        {"pf": pf, "today": today}
    ).mappings().one_or_none()

def log_check_in(conn: Connection, pf: str, now: datetime, today: date):
    """Creates a new attendance entry."""
    conn.execute(
        text("""
            INSERT INTO attendance_logs (pf, arrival_time, date_only)
            VALUES (:pf, :ts, :today)
        """),
        {
        "pf": pf, 
         "ts": now.replace(tzinfo=None), 
         "today": today}
    )

def log_check_out(conn: Connection, pf: str, now: datetime, today: date):
    """Updates an existing entry with a checkout time."""
    result = conn.execute(
        text("""
            UPDATE attendance_logs 
            SET checkout_time = :ts 
            WHERE pf = :pf 
              AND date_only = :today 
              AND checkout_time IS NULL
        """),
        {   
            "ts": now.replace(tzinfo=None),
            "pf": pf,
            "today": today}
    )
    return result.rowcount > 0