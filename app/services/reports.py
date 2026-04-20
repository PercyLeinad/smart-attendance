from sqlalchemy import text
from app.core.database import engine


def get_attendance_report(start_date, end_date):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
            SELECT 
                UPPER(e.pf) AS Pf,
                UPPER(e.name) AS Name,
                UPPER(d.code) AS "Department Code",
                UPPER(d.name) AS "Department Name",
                UPPER(a.arrival_time) AS Arrival,
                UPPER(a.checkout_time) AS Checkout
            FROM attendance_logs AS a
            INNER JOIN employees AS e 
                ON e.pf = a.pf
            INNER JOIN departments AS d
                ON e.department_code = d.code
            WHERE a.date_only BETWEEN :start_date AND :end_date
            ORDER BY a.arrival_time DESC
            """),
            {
                "start_date": start_date,
                "end_date": end_date
            }
        )

        return [dict(row) for row in result.mappings()]