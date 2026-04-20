from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from app.web.routes.auth import is_admin
from app.services.reports import get_attendance_report

router = APIRouter(
    dependencies=[Depends(is_admin)]
)

# -----------------------------
# Export CSV Report
# -----------------------------
@router.get("/admin/report/export")
def export_data(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    # 🔥 Use service (no SQL here anymore)
    data = get_attendance_report(start_date, end_date)

    df = pd.DataFrame(data)

    # Ensure reports folder exists
    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    # Generate filename
    today_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"attendance_report_{today_str}.csv"
    file_path = reports_folder / filename

    # Save CSV
    df.to_csv(file_path, index=False)

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename
    )


# -----------------------------
# Get Report Data (for UI)
# -----------------------------
@router.get("/admin/report")
def report_by_range(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    # 🔥 Same service reused
    data = get_attendance_report(start_date, end_date)
    return data