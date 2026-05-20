import logging
import os
import pathlib
from dotenv import load_dotenv
import requests
import json

# Setup file pathways relative to script location
cwd = pathlib.Path(__file__).parent
log_file_path = cwd / 'sync_employees.log'  # Or route to absolute path /var/log/dbsync/sync_employees.log

load_dotenv(dotenv_path=cwd / '.env')

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()  # Keeps cron redirection working
    ]
)
logger = logging.getLogger("sync_employees")

def fetch_employees():
    url = os.getenv("API_URL")
    headers = {"Authorization": os.getenv("API_AUTHORIZATION_TOKEN")}
    
    logger.info("Initiating API request to fetch employees data...")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status() 
    return response.json()

def save_json_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Successfully cached dataset payload to file path: {filename}")

if __name__ == "__main__":
    try:
        employees = fetch_employees()
        cache_target = cwd / "employees.json"
        save_json_to_file(employees, cache_target)
        logger.info(f"Sync script complete. Processed {len(employees)} records total from remote API source.")
    except requests.exceptions.RequestException as re:
        logger.error(f"Network operations error talking to remote API endpoint resource: {re}")
    except Exception as e:
        logger.error("Critical failure during API ingestion orchestration phase", exc_info=True)