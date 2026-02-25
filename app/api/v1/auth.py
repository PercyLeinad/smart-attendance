import re
from passlib.context import CryptContext
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

pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__memory_cost=102400,
    argon2__time_cost=2,
    argon2__parallelism=8,
    deprecated="auto"
)
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

    # Validate credentials using bcrypt
    if not db_password or not pwd_context.verify(password, db_password):
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
        
        "admin.html",
        {
            "request": request,
            "stats": stats
        }
    )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# 1. Page to List Admins
@router.get("/admin/masters", response_class=HTMLResponse)
async def masters_page(request: Request, admin: str = Depends(is_admin)):
    with engine.connect() as conn:
        # We don't select the password for the UI
        admins = conn.execute(
            text("SELECT username,CreationDate FROM masters ORDER BY CreationDate DESC")
        ).mappings().all()
    
    return templates.TemplateResponse("masters.html", {
        "request": request, 
        "admins": admins
    })

# 2. Add New Admin
@router.post("/admin/masters/add")
async def add_master(
    request: Request, # You need the request object for templates
    username: str = Form(...),
    password: str = Form(...),
    admin: str = Depends(is_admin),
):
    # 1. Collect errors in a list or check them one by one
    error = None
    if len(password) < 8:
        error = "Password must be at least 8 characters."
    elif not re.search(r"[A-Z]", password):
        error = "Password must contain an uppercase letter."
    elif not re.search(r"[0-9]", password):
        error = "Password must contain a number."

    # 2. If there's an error, re-render the original form page
    if error:
        return templates.TemplateResponse(
            "masters.html", 
            {"request": request, 
             "error": error, 
             "username": username})  

    hashed_password = pwd_context.hash(password)
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO masters (username, password) VALUES (:u, :p)"),
                {"u": username, "p": hashed_password}
            )
        return RedirectResponse(url="/admin/masters", status_code=303)

    except Exception:
        return templates.TemplateResponse(
            "masters.html", 
            {"request": request, "error": "Username already exists.", "username": username}
        )

# 3. Delete Admin
@router.post("/admin/masters/delete/{username}")
async def delete_master(
    username: str,
    admin: str = Depends(is_admin)
):
    if username == admin:
        return RedirectResponse(
            url="/admin/masters?error=You cannot delete your own account.",
            status_code=303
        )

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM masters WHERE username = :u"),
            {"u": username}
        )

    return RedirectResponse(url="/admin/masters", status_code=303)



@router.post("/admin/masters/change-password")
async def change_password(
    request: Request,
    username: str = Form(...),
    new_password: str = Form(...),
    admin: str = Depends(is_admin)
):
    # 1. Validation Logic
    error = None
    if len(new_password) < 8:
        error = "New password must be at least 8 characters."
    elif not re.search(r"[A-Z]", new_password):
        error = "New password must contain an uppercase letter."
    
    if error:
        with engine.connect() as conn:
            admins = conn.execute(text("SELECT username, CreationDate FROM masters")).fetchall()
        return templates.TemplateResponse("masters.html", {
            "request": request, 
            "admins": admins, 
            "error": error
        })

    # 2. Update Database
    hashed_password = pwd_context.hash(new_password)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE masters SET password = :p WHERE username = :u"),
            {"p": hashed_password, "u": username}
        )
    
    return RedirectResponse(url="/admin/masters", status_code=303)