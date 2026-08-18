from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.database import engine
from app.services.smtp import get_user
from dotenv import load_dotenv
import os
from app.core.redis import redis_client
from datetime import datetime, time
from fastapi import Request
from app.core.tokens import TokenService

load_dotenv()

router = APIRouter()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

class SendLinkRequest(BaseModel):
    pf: str
    
@router.post("/send-link")
def send_qr_link_email(data: SendLinkRequest, request: Request):
    # 1. TIME GATE: Enforce 8:00 AM to 5:00 PM (17:00) window
    current_time = datetime.now().time()
    start_time = time(8, 0)
    end_time = time(17, 0)

    if not (start_time <= current_time <= end_time):
        raise HTTPException(
            status_code=403,
            detail="Access link requests are only permitted between 8:00 AM and 5:00 PM."
        )

    # 2. DAILY CAP RATE LIMITING (Max 2 requests per calendar day)
    current_date = datetime.now().strftime("%Y-%m-%d")
    rate_limit_key = f"email_requests:{data.pf}:{current_date}"

    # Check request count BEFORE incrementing to prevent bypassing
    current_count = int(redis_client.get(rate_limit_key) or 0)
    if current_count >= 2:
        raise HTTPException(
            status_code=429,
            detail="You have reached your maximum allowance of 2 email requests for today."
        )

    # 3. DATABASE VERIFICATION
    with engine.connect() as connection:
        user_row = get_user(connection, data.pf)

    if not user_row:
        raise HTTPException(status_code=404, detail="No such user found in the system.")

    to_email = user_row.email if user_row.email else user_row.personal_email

    if not to_email:
        raise HTTPException(
            status_code=422,
            detail="User found, but no email address is registered on your account."
        )

    # 4. INCREMENT COUNTER & SET EXPIRATION (Only for valid users)
    request_count = redis_client.incr(rate_limit_key)
    if request_count == 1:
        # Calculate seconds until midnight so key expires automatically at 00:00:00
        now = datetime.now()
        midnight = datetime.combine(now.date(), time(23, 59, 59))
        seconds_until_midnight = max(1, int((midnight - now).total_seconds()))
        redis_client.expire(rate_limit_key, seconds_until_midnight)

    # 5. DISPATCH SMTP MAIL
    base_url = str(request.base_url).rstrip("/")
    token = TokenService.create_email_token(data.pf)
    email_link = f"{base_url}/email-access/{token}"

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = "Attendance Link"

    html_body = f"""
    <html>
      <body>
        <p>Hello,</p>
        <p>You have requested an access link.</p>
        <p>Please use the link below:</p>
        <p><a href="{email_link}" style="font-weight: bold; color: #10b981;">{email_link}</a></p>
        <p><em>Note: This link is time-sensitive and will expire shortly.</em></p>
        <br>
        <p style="font-size: 11px; color: #6b7280;">This is an automated system notification. Please do not reply to this email.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        return {"message": "Email sent successfully"}

    except Exception as e:
        # Roll back counter if SMTP fails so user doesn't lose a valid attempt
        redis_client.decr(rate_limit_key)
        raise HTTPException(status_code=500, detail="Failed to send email. Please try again later.")