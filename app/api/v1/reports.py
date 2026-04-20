from fastapi import APIRouter, Query
from datetime import date
from app.services.reports import get_attendance_report

router = APIRouter()

@router.get("/reports")
def get_reports(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    data = get_attendance_report(start_date, end_date)
    return {
        "count": len(data),
        "data": data
    }