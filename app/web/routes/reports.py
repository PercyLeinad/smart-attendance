from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from app.web.routes.auth import is_admin
from app.services.reports import get_attendance_report, get_device_risk_report
from app.schemas.device import DeviceRiskReportResponse

router = APIRouter(
    dependencies=[Depends(is_admin)]
)
# -----------------------------
# Get Report Data (for UI)
# -----------------------------
@router.get("/admin/report/attendance")
def report_by_range(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    # 🔥 Same service reused
    data = get_attendance_report(start_date, end_date)
    return data

# -----------------------------
# Export CSV Report
# -----------------------------
@router.get("/admin/report/attendance/export")
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

@router.get(
    "/admin/report/device-risk",
    response_model=DeviceRiskReportResponse
)
def device_risk_report():
    data = get_device_risk_report()
    return {"data": data}
    

@router.get(
    "/admin/report/device-risk/export"
)
def device_risk_report_export():
    data = get_device_risk_report()
    df = pd.DataFrame(data)

    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"device_risk_report_{today_str}.csv"
    file_path = reports_folder / filename

    df.to_csv(file_path, index=False)

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename
    )

if '__name__' == '__main__':
    reports_folder = Path("reports")
    print(reports_folder)