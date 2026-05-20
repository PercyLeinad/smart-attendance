import json
import re
import pathlib
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Employee
from app.core.database import DATABASE_URL as DB_URL

# Setup Logging Environment Layout
cwd = pathlib.Path(__file__).parent
log_file_path = cwd / "logs" / "db_sync.log"  # Or route to absolute path /var/log/dbsync/db_sync.log

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("db_sync")

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

MASTER_DATA = []

def load_json_file(file_path):
    logger.info(f"Reading employee cache storage target file from location: {file_path}")
    with open(file_path, 'r') as file:
        return json.load(file)
    
def extract_pf_employees():
    try:
        employees = load_json_file(cwd / 'employees.json')
        for employee in employees:
            # Match 4 digits starting with 0
            if re.match(r'0\d{3}$', str(employee.get('Pf', ''))) and employee.get('Status') == "Active":
                MASTER_DATA.append(employee)
        logger.info(f"Pre-filtering execution stage complete. Extracted {len(MASTER_DATA)} active tracking profiles.")
    except FileNotFoundError:
        logger.error(f"Failed to extract matching employee profiles: 'employees.json' cache layout is missing.")
        raise

def clean_str(value):
    if value is None:
        return None
    value = str(value).replace('\xa0', ' ').strip()
    if value == "" or value.lower() in ["null", "none", "undefined"]:
        return None
    return value

def sync_employees():
    session = SessionLocal()
    skipped_count = 0
    synced_count = 0

    try:
        logger.info("Initializing relational schema updates loop iteration sequence...")
        with session.no_autoflush:
            for item in MASTER_DATA:
                clean_item = {str(k).strip().lower(): v for k, v in item.items()}

                name = clean_str(clean_item.get("name"))
                department_code = clean_str(clean_item.get("department_code"))
                company_email = clean_str(clean_item.get("company_email"))
                personal_email = clean_str(clean_item.get("personal_email"))
                id_number = clean_str(clean_item.get("id_number"))
                pf = clean_str(clean_item.get("pf"))

                if not pf:
                    continue  
                
                if not department_code:
                    logger.warning(f"Skipping profile update record for PF {pf} ({name or 'Unknown Name'}): Missing department foreign reference assignment value.")
                    skipped_count += 1
                    continue  

                employee = session.get(Employee, pf)
                if not employee:
                    logger.debug(f"Allocating staging space initialization footprint instance structures for unknown novel primary tracker identity PF: {pf}")
                    employee = Employee(pf=pf)
                    session.add(employee)

                employee.name = name
                employee.department_code = department_code
                employee.email = company_email
                employee.personal_email = personal_email
                employee.id_number = id_number

                status = clean_str(clean_item.get("status")) or "Active"
                employee.status = status.capitalize()
                
                synced_count += 1

        # Commit everything safely at the very end
        session.commit()
        logger.info("--- Data Store Engine Processing Sync Sequence Complete ---")
        logger.info(f"Execution report summary stats: Successfully synced={synced_count} entries | Skipped anomalies={skipped_count}")

    except Exception as e:
        session.rollback()
        logger.error("Transactional block execution failure, changes rolled back.", exc_info=True)

    finally:
        session.close()

if __name__ == "__main__":
    try:
        extract_pf_employees()
        if MASTER_DATA:
            sync_employees()
        else:
            logger.warning("Aborting execution routine sequence early: Master data array is empty.")
    except Exception as critical_err:
        logger.critical(f"Process terminated context block failure: {critical_err}")