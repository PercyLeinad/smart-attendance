from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pyotp
from datetime import datetime
from core.database import engine
from sqlalchemy import text
from core.ui import BASE_DIR
from schemes.attendance import AttendanceRequest
from fastapi import Query

router = APIRouter()
SHARED_SECRET = "JBSWY3DPEHPK3PXP"
totp = pyotp.TOTP(SHARED_SECRET, interval=120,digits=6)  # QR code changes every 30 seconds

router.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@router.get("/get-current-qr-token")
def get_qr_token():
    return {"token": totp.now()}

@router.get("/display")
def serve_display():
    return FileResponse(str(BASE_DIR / "templates" / "display.html"))

@router.post("/check-in")
async def check_in(data: AttendanceRequest):

    if not totp.verify(data.token, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid or Expired QR Code.")

    now = datetime.now()
    today = now.date()

    with engine.begin() as conn:

        # 🔹 Resolve PF from either PF or ID input
        res = conn.execute(
            text("""
                SELECT name, pf 
                FROM employees 
                WHERE id_number = :sid OR pf = :sid
            """),
            {"sid": data.staff_id}
        ).mappings().one_or_none()

        if not res:
            raise HTTPException(status_code=404, detail="Staff not found.")

        full_name = res["name"]
        pf_number = res["pf"]  # ✅ ALWAYS use this after lookup, id or pf is consolidated to pf_number

        # 🔹 Check today's record USING REAL PF
        record = conn.execute(
            text("""
                SELECT arrival_time, checkout_time
                FROM attendance_logs
                WHERE pf = :pf
                AND date_only = :today
                LIMIT 1
            """),
            {"pf": pf_number, "today": today}
        ).mappings().one_or_none()

        # 1️⃣ No record → CHECK IN
        if not record:
            conn.execute(
                text("""
                    INSERT INTO attendance_logs (pf, arrival_time, date_only)
                    VALUES (:pf, :ts, :today)
                """),
                {"pf": pf_number, "ts": now, "today": today}
            )
            return {"status": "checked_in", "staff": full_name}

        # 2️⃣ Already completed
        if record["arrival_time"] and record["checkout_time"]:
            return {"status": "completed", "staff": full_name}

        # 3️⃣ Needs checkout
        if record["checkout_time"] is None:
            
            if not data.confirm:
                return {"status": "confirm_checkout", "staff": full_name}

            result = conn.execute(
                text("""
                    UPDATE attendance_logs 
                    SET checkout_time = :ts 
                    WHERE pf = :pf 
                      AND date_only = :today 
                      AND checkout_time IS NULL
                """),
                {"ts": now, "pf": pf_number, "today": today}
            )

            if result.rowcount > 0:
                return {"status": "checked_out", "staff": full_name}
            else:
                # This handles the race condition where someone might have 
                # updated it between the SELECT and UPDATE
                return {"status": "completed", "staff": full_name}

