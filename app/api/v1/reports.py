
from fastapi.responses import FileResponse
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from core.database import engine
from fastapi import APIRouter, Depends
from fastapi import APIRouter, Query
from datetime import date
from api.v1.auth import is_admin

router = APIRouter(
    dependencies=[Depends(is_admin)]
)
# router = APIRouter()
# -----------------------------
# Export CSV Report
# -----------------------------
from fastapi import Query
from datetime import date

@router.get("/admin/report/export")
def export_data(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    with engine.connect() as connection:
        query = text("""
            SELECT 
                e.name,
                e.pf,
                d.name AS department_name,
                a.arrival_time,
                a.checkout_time
            FROM attendance_logs AS a
            INNER JOIN employees AS e 
                ON e.pf = a.pf
            INNER JOIN departments AS d
                ON e.department_code = d.code
            WHERE a.date_only BETWEEN :start_date AND :end_date
            ORDER BY a.arrival_time DESC
        """)

        result = connection.execute(
            query,
            {
                "start_date": start_date,
                "end_date": end_date
            }
        )

        rows = [dict(row) for row in result.mappings()]

    df = pd.DataFrame(rows)

    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"attendance_report_{today_str}.csv"
    file_path = reports_folder / filename

    df.to_csv(file_path, index=False)

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename
    )


@router.get("/admin/report")
def report_by_range(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT pf, COUNT(*) as days_present
                FROM attendance_logs
                WHERE date_only BETWEEN :start_date AND :end_date
                GROUP BY pf
            """),
            {
                "start_date": start_date,
                "end_date": end_date
            }
        )

        data = [dict(row) for row in result.mappings()]

    return data
