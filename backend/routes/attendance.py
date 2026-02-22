from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pyotp
from datetime import datetime
from backend.db_conn import engine
from sqlalchemy import text

router = APIRouter()
SHARED_SECRET = "JBSWY3DPEHPK3PXP"
totp = pyotp.TOTP(SHARED_SECRET, interval=30)

class AttendanceRequest(BaseModel):
    staff_id: str
    token: str

@router.get("/get-current-qr-token")
def get_qr_token():
    return {"token": totp.now()}

@router.post("/check-in")
async def check_in(data: AttendanceRequest):
    # 1. Validation (Outside the DB try/except)
    if not totp.verify(data.token, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid or Expired QR Code.")
    
    # 2. Database Operations
    try:
        with engine.begin() as conn:  # .begin() automatically handles commits/rollbacks
            # Verify Staff
            res = conn.execute(
                text("SELECT Name, pf FROM employees WHERE id_number = :sid OR pf = :sid"), 
                {"sid": data.staff_id}
            ).mappings().one_or_none()

            if not res:
                # This bypasses the 'except' block if we raise it specifically or 
                # we handle the exception logic better.
                raise HTTPException(status_code=404, detail="Staff ID not registered.")

            full_name = res['Name']
            pf_number = res['pf'] # Use the actual PF from DB to ensure data integrity
            now = datetime.now()
            today = now.date()

            # Check existing record
            record = conn.execute(
                text("SELECT id, checkout_time FROM attendance_logs WHERE pf = :pf AND date_only = :today"),
                {"pf": pf_number, "today": today}
            ).mappings().one_or_none()

            # Logic branches
            if not record:
                conn.execute(
                    text("INSERT INTO attendance_logs (pf, arrival_time, date_only) VALUES (:pf, :ts, :today)"),
                    {"pf": pf_number, "ts": now, "today": today}
                )
                return {"status": "checked_in", "staff": full_name, "time": now}

            if record['checkout_time'] is None:
                conn.execute(
                    text("UPDATE attendance_logs SET checkout_time = :ts WHERE id = :id"),
                    {"ts": now, "id": record['id']}
                )
                return {"status": "checked_out", "staff": full_name, "time": now}

            raise HTTPException(status_code=400, detail="Attendance already completed.")

    except HTTPException:
        # Re-raise our own 400/404 errors so they aren't caught by the 500 block
        raise
    except Exception as e:
        # Log the real error to your console, but give the user a generic 500
        print(f"Database Crash: {e}") 
        raise HTTPException(status_code=500, detail="A database error occurred.")
        
@router.get("/display")
def serve_display():
    return FileResponse("static/display.html")