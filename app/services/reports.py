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

def get_device_risk_report():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
            SELECT 
                e.pf AS staff_pf,
                UPPER(e.name) AS name,

                /* =========================
                   DEVICE METRICS
                ========================== */

                /* fingerprint_hash is now derived from stable device_id */
                COUNT(DISTINCT d.fingerprint_hash) AS device_count,

                /* Informational only — not part of device identity */
                GREATEST(COUNT(DISTINCT d.ip_address) - 1, 0) AS ip_changes,

                /* Shared device detection */
                MAX(
                    CASE 
                        WHEN COALESCE(sd.shared_users, 0) > 1 THEN 1
                        ELSE 0
                    END
                ) AS shared_device_flag,

                /* Convert UTC to local time */
                CONVERT_TZ(
                    MAX(d.last_seen),
                    '+00:00',
                    :tz_offset
                ) AS last_seen,

                /* =========================
                   DEVICE RISK SCORE
                ========================== */
                (
                    /* Multiple devices */
                    CASE
                        WHEN COUNT(DISTINCT d.fingerprint_hash) <= 1 THEN 0
                        WHEN COUNT(DISTINCT d.fingerprint_hash) = 2 THEN 2
                        WHEN COUNT(DISTINCT d.fingerprint_hash) <= 4 THEN 5
                        ELSE 10
                    END

                    +

                    /* Device used by multiple staff members */
                    CASE
                        WHEN MAX(
                            CASE
                                WHEN COALESCE(sd.shared_users, 0) > 1 THEN 1
                                ELSE 0
                            END
                        ) = 1
                        THEN 10
                        ELSE 0
                    END
                ) AS risk_score

            FROM devices d

            INNER JOIN employees e 
                ON e.pf COLLATE utf8mb4_general_ci
                = d.staff_pf COLLATE utf8mb4_general_ci

            /* Count how many different staff use each device */
            LEFT JOIN (
                SELECT 
                    fingerprint_hash,
                    COUNT(DISTINCT staff_pf) AS shared_users
                FROM devices
                GROUP BY fingerprint_hash
            ) sd 
                ON sd.fingerprint_hash COLLATE utf8mb4_general_ci
                = d.fingerprint_hash COLLATE utf8mb4_general_ci

            GROUP BY e.pf, e.name

            ORDER BY risk_score DESC, last_seen DESC
            """),
            {
                "tz_offset": "+03:00"
            }
        )

    return [dict(row) for row in result.mappings()]