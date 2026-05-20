import json
import re
import pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Employee
from app.core.database import DATABASE_URL as DB_URL

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

MASTER_DATA = []

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    
def extract_pf_employees():
    cwd = pathlib.Path(__file__).parent
    employees = load_json_file(cwd / 'employees.json')
    for employee in employees:
        if re.match(r'0\d{3}$', employee['Pf']) and employee.get('Status') == "Active":
            MASTER_DATA.append(employee)

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
        # Wrap the loop in no_autoflush to prevent premature db validation crashes
        with session.no_autoflush:
            for item in MASTER_DATA:
                # Normalize keys to lowercase
                clean_item = {str(k).strip().lower(): v for k, v in item.items()}

                # Clean and normalize fields
                name = clean_str(clean_item.get("name"))
                department_code = clean_str(clean_item.get("department_code"))
                company_email = clean_str(clean_item.get("company_email"))
                personal_email = clean_str(clean_item.get("personal_email"))
                id_number = clean_str(clean_item.get("id_number"))
                pf = clean_str(clean_item.get("pf"))

                if not pf:
                    continue  
                
                # Skip if department code is completely missing
                if not department_code:
                    print(f"Skipping employee PF {pf} ({name}): Missing department code.")
                    skipped_count += 1
                    continue  

                # Fetch or initialize the employee
                employee = session.get(Employee, pf)
                if not employee:
                    employee = Employee(pf=pf)
                    session.add(employee)

                # Assign normalized fields
                employee.name = name
                employee.department_code = department_code
                employee.email = company_email
                employee.personal_email = personal_email
                employee.id_number = id_number

                # Status
                status = clean_str(clean_item.get("status")) or "Active"
                employee.status = status.capitalize()
                
                synced_count += 1
                print(employee)

        # Commit everything safely at the very end
        session.commit()
        print(f"--- Sync Complete ---")
        print(f"Successfully synced: {synced_count} employees")
        print(f"Skipped:             {skipped_count} employees")

    except Exception as e:
        session.rollback()
        print(f"Sync failed completely: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    extract_pf_employees()
    sync_employees()