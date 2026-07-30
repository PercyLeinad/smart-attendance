import os
from dotenv import load_dotenv
import pyotp
from itsdangerous import URLSafeTimedSerializer

load_dotenv()
    
# Shared QR token
QR_SECRET = os.getenv("SHARED_SECRET")

if not QR_SECRET:
    raise RuntimeError("SHARED_SECRET not set")

qr_totp = pyotp.TOTP(QR_SECRET, interval=45, digits=10)

# Email token signer
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set")

serializer = URLSafeTimedSerializer(SECRET_KEY)


class TokenService:

    # ---------- QR TOKEN ----------

    @staticmethod
    def current_qr_token() -> str:
        return qr_totp.now()

    @staticmethod
    def verify_qr_token(token: str) -> bool:
        return qr_totp.verify(token, valid_window=1)

    # ---------- EMAIL TOKEN ----------

    @staticmethod
    def create_email_token(pf: str) -> str:
        return serializer.dumps({"pf": pf}, salt="email-access")

    @staticmethod
    def verify_email_token(token: str, max_age: int = 120) -> dict:
        return serializer.loads(
            token,
            salt="email-access",
            max_age=max_age
        )