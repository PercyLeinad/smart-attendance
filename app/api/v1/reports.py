from datetime import date
from app.services.reports import get_attendance_report
from fastapi import APIRouter, Query, Depends, HTTPException, status, Request
router = APIRouter()

MAX_RANGE = 30 # days

# Prevent injection and limit ranges:
def validate_dates(start: date, end: date):
    if end < start:
        raise HTTPException(400, "Invalid date range")
    if (end - start).days > MAX_RANGE:
        raise HTTPException(400, f"Max range is {MAX_RANGE} days")
    return start, end

@router.get("/reports")
def get_reports(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    start_date, end_date = validate_dates(start_date, end_date)
    data = get_attendance_report(start_date, end_date)
    return {
        "count": len(data),
        "data": data
    }