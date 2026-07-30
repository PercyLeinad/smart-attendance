from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from datetime import UTC, datetime
from app.schemas.attendance import AttendanceRequest
from app.core.database import engine
from app.core.ui import BASE_DIR
from app.services import attendance as attendance_service
from app.services.fingerprint import log_device
from app.core.tokens import TokenService
from fastapi.responses import RedirectResponse
from itsdangerous import SignatureExpired, BadSignature
from app.core.redis import redis_client
from app.core.status import status_page

router = APIRouter()

# moved this to nginx or apache for production, but you can uncomment for development
# router.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

@router.get("/get-current-qr-token") 
def get_qr_token(): 
    return {"token": TokenService.current_qr_token()}

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
    if not TokenService.verify_qr_token(data.token):
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
            


@router.get("/email-access/{token}")
def email_access(token: str):

    try:
        data = TokenService.verify_email_token(token, max_age=120) # SINGLE-USE CHECK HERE 
        used_key = f"email-used:{token}" 
        if redis_client.exists(used_key): 
            return status_page( title="Link Already Used", message="This attendance link has already been used and cannot be used again.", icon="🔒", button_text="Request Another Link", button_color="#f59e0b" )
        redis_client.setex(used_key, 120, "1") 
        pf = data["pf"] 
        qr_token = TokenService.current_qr_token() 
        return RedirectResponse( url=f"/scan?token={qr_token}&pf={pf}&email=1", status_code=302 )

    except SignatureExpired: 
        return status_page( title="Link Expired", message="This attendance link has expired for your security. Please request a new link from the attendance display.", icon="⏰", button_text="Request New Link", button_color="#10b981" )
    except BadSignature: 
        return status_page( title="Invalid Link", message="This attendance link is invalid or has been tampered with. Please request a new access link from the attendance display.", icon="⚠️", button_text="Go to Attendance Display", button_color="#2563eb" )