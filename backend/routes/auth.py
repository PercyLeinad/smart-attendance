from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from backend.db_conn import engine
from sqlalchemy import text

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 1. This handles the BROWSER loading the page (Fixes the 405)
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT password FROM masters WHERE username = :username"), {"username": username})
        admin = result.fetchone()

    if not admin:
        return RedirectResponse("/login", status_code=302)

    db_password = admin[0]

    # For now plain text (we upgrade later)
    if password != db_password:
         return RedirectResponse(url="/login?msg=error", status_code=303)

    request.session["admin"] = username

    return RedirectResponse("/admin", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    # This clears the session cookie entirely
    request.session.clear() 
    # Redirect to login page with a 303 (See Other) status
    return RedirectResponse(url="/login", status_code=303)
