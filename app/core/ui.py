from pathlib import Path
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent  # points to /app

templates = Jinja2Templates(
    directory=str(BASE_DIR / "web" / "templates")
)

if __name__ == "__main__":
    print(f"BASE_DIR: {BASE_DIR}")