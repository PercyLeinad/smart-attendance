import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
import pyotp
from datetime import UTC, datetime
from app.schemas.attendance import AttendanceRequest
from dotenv import load_dotenv
from app.core.database import engine
from app.core.ui import BASE_DIR
from app.services import attendance as attendance_service
from app.services.fingerprint import log_device
# Load environment variables from .env
load_dotenv()

router = APIRouter()

SHARED_SECRET = os.getenv("SHARED_SECRET")
if not SHARED_SECRET:
    raise ValueError("SHARED_SECRET environment variable is not set.")

totp = pyotp.TOTP(SHARED_SECRET, interval=45,digits=10)  # QR code changes every 45 seconds

# moved this to nginx or apache for production, but you can uncomment for development
# router.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

@router.get("/get-current-qr-token")
def get_qr_token():
    return {"token": totp.now()}

@router.get("/display")
def serve_display():
    return FileResponse(str(BASE_DIR / "web" / "templates" / "display.html"))

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"

@router.post("/check-in")
async def check_in(data: AttendanceRequest, request: Request):
    # External Security Check (TOTP)
    if not totp.verify(data.token, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid or Expired QR Code.")

    now = datetime.now(UTC)
    today = now.date()
    ip_address = get_client_ip(request)

    with engine.begin() as conn:
        # Identify the Staff
        staff = attendance_service.get_employee_by_id_or_pf(conn, data.staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found.")

        full_name = staff["name"]
        pf_number = staff["pf"]

        # Check for existing logs FIRST
        record = attendance_service.get_attendance_record(conn, pf_number, today)
        
        # -------------------------------
        # First time check-in
        # -------------------------------
        if not record:
            attendance_service.log_check_in(conn, pf_number, now, today)

            log_device(
                conn,
                pf_number=pf_number,
                device_info=data.device_info,
                ip_address=ip_address
            )  # ✅ log once here

            return {"status": "checked_in", "staff": full_name}

        # -------------------------------
        # Already completed
        # -------------------------------
        if record["arrival_time"] and record["checkout_time"]:
            return {"status": "completed", "staff": full_name}

        # -------------------------------
        # Checkout flow
        # -------------------------------
        if record["checkout_time"] is None:
            # Step 1: Ask for confirmation (NO logging here)
            if not data.confirm:
                return {"status": "confirm_checkout", "staff": full_name}

            # Step 2: Confirmed checkout
            updated = attendance_service.log_check_out(conn, pf_number, now, today)

            if updated:
                log_device(
                    conn,
                    pf_number=pf_number,
                    device_info=data.device_info,
                    ip_address=ip_address
                )  # ✅ log only on confirmed action
                return {"status": "checked_out", "staff": full_name}
            else:
                return {"status": "completed", "staff": full_name}