from fastapi import APIRouter, Form, HTTPException, Request,status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from core.database import engine
from sqlalchemy import text
from core.ui import templates

# -----------------------------
def is_admin(request: Request):
    admin = request.session.get("admin")
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"}
        )
    return admin

router = APIRouter()

# -----------------------------
# Login Page
# -----------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, 
          username: str = Form(...), 
          password: str = Form(...)
          ):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT password FROM masters WHERE username = :username"), {"username": username})
        admin = result.mappings().one_or_none()

    db_password = admin['password'] if admin else None

    if not admin or password != db_password:
         return RedirectResponse(url="/login?msg=invalid_credentials", status_code=303)

    request.session.clear()
    request.session["admin"] = username

    return RedirectResponse("/admin", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear() 
    return RedirectResponse(url="/login", status_code=303)


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: str = Depends(is_admin)):

    with engine.connect() as connection:
        stats = connection.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM employees) AS total_employees,
                (SELECT COUNT(*) FROM attendance_logs WHERE date_only = CURDATE()) AS today_attendance,
                (SELECT COUNT(*) FROM employees WHERE pf NOT LIKE 'CA%') AS permanent,
                (SELECT COUNT(*) FROM employees WHERE pf LIKE 'CA%') AS casuals
        """)).mappings().one()

    response = templates.TemplateResponse(
        
        "dashboard.html",
        {
            "request": request,
            "stats": stats
        }
    )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
