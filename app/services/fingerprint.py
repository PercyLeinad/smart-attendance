import hashlib
from datetime import datetime, UTC
from sqlalchemy import text


def generate_fingerprint(device_id: str) -> str:
    """
    Create a stable fingerprint from the browser's persistent device ID.
    """

    if not device_id:
        raise ValueError("device_id is required")

    return hashlib.sha256(
        device_id.encode("utf-8")
    ).hexdigest()


def log_device(conn, *, pf_number: str, device_info, ip_address: str):
    """
    Inserts a new device or updates an existing device.
    """

    if not device_info:
        return

    # The device ID is now the primary identity.
    # User agent and screen are only device attributes.
    fp_hash = generate_fingerprint(
        device_id=device_info.device_id
    )

    conn.execute(
        text("""
            INSERT INTO devices (
                staff_pf,
                fingerprint_hash,
                user_agent,
                screen_resolution,
                timezone,
                language,
                last_seen,
                ip_address
            )
            VALUES (
                :pf,
                :hash,
                :ua,
                :res,
                :tz,
                :lang,
                :now,
                :ip
            )
            ON DUPLICATE KEY UPDATE
                last_seen = VALUES(last_seen),
                ip_address = VALUES(ip_address),
                user_agent = VALUES(user_agent),
                screen_resolution = VALUES(screen_resolution),
                timezone = VALUES(timezone),
                language = VALUES(language)
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