from sqlalchemy import text
from app.core.database import engine
from datetime import timedelta

def get_attendance_report(start_date, end_date):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
            SELECT 
                UPPER(e.pf) AS Pf,
                UPPER(e.name) AS Name,
                UPPER(d.code) AS "Department Code",
                UPPER(d.name) AS "Department Name",
                DATE_FORMAT(
                        CONVERT_TZ(a.arrival_time, '+00:00', :tz_offset),
                        '%Y-%m-%d %H:%i:%s'
                    ) AS Arrival,
                DATE_FORMAT(
                        CONVERT_TZ(a.checkout_time, '+00:00', :tz_offset),
                        '%Y-%m-%d %H:%i:%s'
                    ) AS Checkout
            FROM attendance_logs AS a
            INNER JOIN employees AS e 
                ON e.pf = a.pf
            INNER JOIN departments AS d
                ON e.department_code = d.code
            WHERE a.date_only BETWEEN :start_date AND :end_date
            ORDER BY a.arrival_time ASC
            """),
            {
                "start_date": start_date,
                "end_date": end_date,
                "tz_offset": "+03:00" # Or pass the timezone name if your DB has tz tables loaded
            }
        )

        return [dict(row) for row in result.mappings()]

"""
- Device fingerprints (×2) – counts how many unique device identities are used. 
    More fingerprints suggest possible spoofing or multiple devices.
- IP addresses (×1) – counts how many different networks are used. 
    Frequent changes may indicate VPN or unusual access patterns.
- Shared usage (×5) – checks if the device is used by more than one user. 
    This is heavily weighted as it strongly suggests account sharing or misuse.
"""

def get_device_risk_report(start_date, end_date):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
            SELECT 
                e.pf AS staff_pf,
                UPPER(e.name) AS name,

                /* DEVICE METRICS */
                COUNT(DISTINCT d.fingerprint_hash) AS device_count,
                COUNT(DISTINCT d.ip_address) - 1 AS ip_changes,

                /* Shared device detection */
                MAX(CASE 
                    WHEN sd.shared_users > 1 THEN 1 
                    ELSE 0 
                END) AS shared_device_flag,

                /* ✅ Convert UTC to Local Time here */
                CONVERT_TZ(MAX(d.last_seen), '+00:00', :tz_offset) AS last_seen,

                /* =========================
                   RISK SCORE (DEVICE ONLY)
                ========================== */
                (
                    (COUNT(DISTINCT d.fingerprint_hash) * 2) +
                    (COUNT(DISTINCT d.ip_address) * 1) +
                    (MAX(CASE WHEN sd.shared_users > 1 THEN 1 ELSE 0 END) * 5)
                ) AS risk_score

            FROM devices d

            INNER JOIN employees e 
                ON e.pf COLLATE utf8mb4_general_ci 
                = d.staff_pf COLLATE utf8mb4_general_ci

            /* shared device detection subquery */
            LEFT JOIN (
                SELECT 
                    fingerprint_hash,
                    COUNT(DISTINCT staff_pf) AS shared_users
                FROM devices
                GROUP BY fingerprint_hash
            ) sd 
                ON sd.fingerprint_hash COLLATE utf8mb4_general_ci 
                = d.fingerprint_hash COLLATE utf8mb4_general_ci

            /* ✅ index-friendly date filtering */
            WHERE d.last_seen >= :start_date
              AND d.last_seen < :end_date_plus_one

            GROUP BY e.pf, e.name

            ORDER BY risk_score DESC, last_seen DESC
            """),
            {
                "start_date": start_date,
                "end_date_plus_one": end_date + timedelta(days=1),
                "tz_offset": "+03:00" # Or pass the timezone name if your DB has tz tables loaded
            }
        )

    return [dict(row) for row in result.mappings()]