import hashlib
from datetime import datetime, UTC
from sqlalchemy import text


def generate_fingerprint(device_id: str, user_agent: str, screen: str):
    fp_string = f"{device_id}|{user_agent}|{screen}"
    return hashlib.sha256(fp_string.encode()).hexdigest()


def log_device(conn, *, pf_number: str, device_info, ip_address: str):
    """
    Inserts or updates device record in DB.
    """

    if not device_info:
        return

    fp_hash = generate_fingerprint(
        device_id=device_info.device_id,
        user_agent=device_info.user_agent,
        screen=device_info.screen_resolution
    )

    conn.execute(
        text("""
            INSERT INTO devices (
                staff_pf, fingerprint_hash, user_agent, 
                screen_resolution, timezone, language, 
                last_seen, ip_address
            )
            VALUES (
                :pf, :hash, :ua, 
                :res, :tz, :lang, 
                :now, :ip
            )
            ON DUPLICATE KEY UPDATE 
                last_seen = :now,
                ip_address = IF(ip_address != :ip, :ip, ip_address)
        """),
        {
            "pf": pf_number,
            "hash": fp_hash,
            "ua": device_info.user_agent,
            "res": device_info.screen_resolution,
            "tz": device_info.timezone,
            "lang": device_info.language,
            "now": datetime.now(UTC),
            "ip": ip_address
        }
    )