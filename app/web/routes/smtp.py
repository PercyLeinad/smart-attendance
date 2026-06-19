from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.database import engine
from app.services.smtp import get_user_email_by_pf
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

class SendLinkRequest(BaseModel):
    pf: str
    qr_link: str


@router.post("/send-link")
def send_qr_link_email(data: SendLinkRequest):

    with engine.connect() as connection:
        to_email = get_user_email_by_pf(connection, data.pf)

    if not to_email:
        raise HTTPException(
            status_code=404,
            detail="No email address found for the supplied PF number."
        )

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = "Attendance Link"

    #  Alternative: Bolded HTML payload format
    html_body = f"""
    <html>
      <body>
        <p>Hello,</p>
        <p>You have requested an access link.</p>
        <p>Please use the link below:</p>
        <p><a href="{data.qr_link}" style="font-weight: bold; color: #10b981;">{data.qr_link}</a></p>
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
        raise HTTPException(status_code=500, detail=str(e))