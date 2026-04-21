import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pyotp
from datetime import datetime
from app.schemas.attendance import AttendanceRequest
from dotenv import load_dotenv
from app.core.database import engine
from app.core.ui import BASE_DIR
from app.services import attendance as attendance_service
# Load environment variables from .env
load_dotenv()

router = APIRouter()

SHARED_SECRET = os.getenv("SHARED_SECRET")
if not SHARED_SECRET:
    raise ValueError("SHARED_SECRET environment variable is not set.")

totp = pyotp.TOTP(SHARED_SECRET, interval=45,digits=10)  # QR code changes every 45 seconds

router.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

@router.get("/get-current-qr-token")
def get_qr_token():
    return {"token": totp.now()}

@router.get("/display")
def serve_display():
    return FileResponse(str(BASE_DIR / "web" / "templates" / "display.html"))

@router.post("/check-in")
async def check_in(data: AttendanceRequest):
    # 1. External Security Check (TOTP)
    if not totp.verify(data.token, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid or Expired QR Code.")

    now = datetime.now()
    today = now.date()

    with engine.begin() as conn:
        # 2. Identify the Staff
        staff = attendance_service.get_employee_by_id_or_pf(conn, data.staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found.")

        full_name = staff["name"]
        pf_number = staff["pf"]

        # 3. Check for existing logs
        record = attendance_service.get_attendance_record(conn, pf_number, today)

        # CASE 1: First time arriving
        if not record:
            attendance_service.log_check_in(conn, pf_number, now, today)
            return {"status": "checked_in", "staff": full_name}

        # CASE 2: Already finished for the day
        if record["arrival_time"] and record["checkout_time"]:
            return {"status": "completed", "staff": full_name}

        # CASE 3: Leaving (Checkout)
        if record["checkout_time"] is None:
            # Require explicit confirmation for checkout
            if not data.confirm:
                return {"status": "confirm_checkout", "staff": full_name}

            updated = attendance_service.log_check_out(conn, pf_number, now, today)
            
            if updated:
                return {"status": "checked_out", "staff": full_name}
            else:
                # Fallback for race conditions
                return {"status": "completed", "staff": full_name}

