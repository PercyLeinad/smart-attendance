import requests
import json

def fetch_employees():
    url = "https://api.must.ac.ke/must22/php/employees.php"
    headers = {"Authorization": "Bearer dskslfmlsfnlsdfmwfwefwfwfwf"}
    response = requests.get(url,headers=headers,timeout=30)
    response.raise_for_status() 
    return response.json()


def save_json_to_file(data, filename="employees.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    try:
        employees = fetch_employees()
        save_json_to_file(employees)
        print(f"Successfully fetched and saved {len(employees)} employees to 'employees.json'.")
    except Exception as e:
        print(f"Error fetching employees: {e}")