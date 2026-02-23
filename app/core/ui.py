from fastapi.templating import Jinja2Templates
from pathlib import Path

# Path logic: app/core/ui.py -> app/ -> templates/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
