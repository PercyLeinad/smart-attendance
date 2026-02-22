from email.mime import text

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pathlib import Path
import pandas as pd
from fastapi.responses import FileResponse
from backend.db_conn import engine
from sqlalchemy import text

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Helper to check if user is logged in
def is_admin(request: Request):
    if "admin" not in request.session:
        raise HTTPException(status_code=303, detail="Not authorized")
    return request.session["admin"]

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    try:
        is_admin(request)
        return templates.TemplateResponse("admin.html", {"request": request})
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)

@router.get("/api/report/weekly")
def weekly_report(admin: str = Depends(is_admin)):# This dependency ensures only logged-in admins can access this endpoint
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT pf, COUNT(*) as days_present
            FROM attendance_logs
            WHERE YEARWEEK(date_only, 1) = YEARWEEK(CURDATE(), 1)
            GROUP BY pf
        """))
    data = [dict(row) for row in result.mappings()]
    return data

@router.get("/api/report/monthly")
def monthly_report(admin: str = Depends(is_admin)):
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT pf, COUNT(*) as days_present
            FROM attendance_logs
            WHERE YEAR(date_only) = YEAR(CURDATE()) AND MONTH(date_only) = MONTH(CURDATE())
            GROUP BY pf
        """))
    data = [dict(row) for row in result.mappings()]
    return data


@router.get("/admin/export")
def export_data(admin: str = Depends(is_admin)):
    # Query all attendance logs
    with engine.connect() as connection:
        query = text("""
            SELECT 
                l.id, 
                l.pf, 
                e.name AS employee_name, 
                e.department_code,
                l.arrival_time, 
                l.checkout_time, 
                l.date_only
            FROM attendance_logs l
            INNER JOIN employees e ON l.pf = e.pf
            ORDER BY l.arrival_time DESC
        """)
        result = connection.execute(query)
        rows = [dict(row) for row in result.mappings()]

    df = pd.DataFrame(rows)

    # Create reports folder if it doesn't exist
    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    # Build filename with today's date
    today_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"attendance_report_{today_str}.csv"
    file_path = reports_folder / filename

    # Save CSV to disk
    df.to_csv(file_path, index=False)

    # Return the file for download
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename
    )
    