from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pyotp
from datetime import datetime
from core.database import engine
from sqlalchemy import text
from core.ui import BASE_DIR
from schemes.attendance import AttendanceRequest

router = APIRouter()
SHARED_SECRET = "JBSWY3DPEHPK3PXP"
totp = pyotp.TOTP(SHARED_SECRET, interval=30)

router.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@router.get("/get-current-qr-token")
def get_qr_token():
    return {"token": totp.now()}

@router.post("/check-in")
async def check_in(data: AttendanceRequest):
    # 1. Validation
    if not totp.verify(data.token, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid or Expired QR Code.")
    
    # 2. Database Operations
    try:
        with engine.begin() as conn:
            # Verify Staff: Lookup via either ID Number or PF Number
            res = conn.execute(
                text("""
                    SELECT name, pf 
                    FROM employees 
                    WHERE id_number = :sid OR pf = :sid
                """), 
                {"sid": data.staff_id}
            ).mappings().one_or_none()

            if not res:
                raise HTTPException(status_code=404, detail="Staff not found in database.")

            full_name = res['name']
            pf_number = res['pf'] 
            now = datetime.now()
            today = now.date()

            # Check existing record for TODAY using the PF number
            record = conn.execute(
                text("""
                    SELECT checkout_time 
                    FROM attendance_logs 
                    WHERE pf = :pf AND date_only = :today
                """),
                {"pf": pf_number, "today": today}
            ).mappings().one_or_none()

            # --- BRANCH 1: New Check-in ---
            if not record:
                conn.execute(
                    text("""
                        INSERT INTO attendance_logs (pf, arrival_time, date_only) 
                        VALUES (:pf, :ts, :today)
                    """),
                    {"pf": pf_number, "ts": now, "today": today}
                )
                return {"status": "checked_in", "staff": full_name, "time": now}

            # --- BRANCH 2: Check-out ---
            # Using PF and ensuring we only update the record that hasn't checked out yet
            if record['checkout_time'] is None:
                conn.execute(
                    text("""
                        UPDATE attendance_logs 
                        SET checkout_time = :ts 
                        WHERE pf = :pf 
                        AND date_only = :today 
                        AND checkout_time IS NULL
                    """),
                    {
                        "ts": now, 
                        "pf": pf_number,
                        "today": today
                    }
                )
                return {"status": "checked_out", "staff": full_name, "time": now}

            # --- BRANCH 3: Already Finished ---
            raise HTTPException(status_code=400, detail="Attendance already completed for today.")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Database Error: {e}") 
        raise HTTPException(status_code=500, detail="A database error occurred.")
        
@router.get("/display")
def serve_display():
    return FileResponse(str(BASE_DIR / "templates" / "display.html"))