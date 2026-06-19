from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.database import engine
from app.services.smtp import get_user_email_by_pf

router = APIRouter()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "pnyaga@must.ac.ke"
SMTP_PASSWORD = "xknadoawxppvvbyt"


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
    msg["Subject"] = "Your Secure Access Link"

    body = f"""
            Hello,

            You have requested an access link.

            Please use the link below:

            {data.qr_link}

            Note: This link is time-sensitive and will expire shortly.
            """

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        return {"message": "Email sent successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))