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