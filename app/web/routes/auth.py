
import re
from passlib.context import CryptContext
from fastapi import APIRouter, Form, HTTPException, Request,status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.ui import templates
from app.core.database import engine
import datetime
from app.services import auth as auth_service
# -----------------------------

SESSION_TIMEOUT = 900  # 15 minutes in seconds

router = APIRouter()

pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__memory_cost=102400,
    argon2__time_cost=2,
    argon2__parallelism=8,
    deprecated="auto"
)

def is_admin(request: Request):
    admin = request.session.get("admin")
    last_activity = request.session.get("last_activity")

    if not admin or not last_activity:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"}
        )

    # Convert stored timestamp back to datetime
    last_activity = datetime.datetime.fromisoformat(last_activity)

    # Check if session expired
    if datetime.datetime.now() - last_activity > datetime.timedelta(seconds=SESSION_TIMEOUT):
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login?msg=session_expired"}
        )

    # Update activity timestamp
    request.session["last_activity"] = datetime.datetime.now().isoformat()

    return admin

# -----------------------------
# Login Page
# -----------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with engine.connect() as conn:
        admin = auth_service.get_admin_password(conn, username)  # 👈 moved

    db_password = admin['password'] if admin else None

    if not db_password or not pwd_context.verify(password, db_password):
        return RedirectResponse(url="/login?msg=invalid_credentials", status_code=303)

    request.session.clear()
    request.session["admin"] = username
    request.session["last_activity"] = datetime.datetime.now().isoformat()

    return RedirectResponse("/admin", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear() 
    return RedirectResponse(url="/login", status_code=303)


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: str = Depends(is_admin)):
    # 1. Fetch the missing data
    with engine.connect() as connection:
        stats = auth_service.get_dashboard_stats(connection)

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
        admins = auth_service.list_all_admins(conn)
    
    return templates.TemplateResponse("masters.html", {
        "request": request, 
        "admins": admins
    })

# 2. Add New Admin
@router.post("/admin/masters/add")
async def add_master(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    admin: str = Depends(is_admin),
):
    error = None

    # Validation
    if len(password) < 8:
        error = "Password must be at least 8 characters."
    elif not re.search(r"[A-Z]", password):
        error = "Password must contain an uppercase letter."
    elif not re.search(r"[0-9]", password):
        error = "Password must contain a number."

    if error:
        return templates.TemplateResponse(
            "masters.html",
            {"request": request, "error": error, "username": username}
        )

    hashed_password = pwd_context.hash(password)

    try:
        with engine.begin() as conn:
            auth_service.add_new_admin(conn, username, email, hashed_password)

        return RedirectResponse(url="/admin/masters", status_code=303)

    except IntegrityError:
        return templates.TemplateResponse(
            "masters.html",
            {
                "request": request,
                "error": "Username already exists",
                "username": username,
                "email": email
            }
        )

    except Exception:
        return templates.TemplateResponse(
            "masters.html",
            {
                "request": request,
                "error": "Something went wrong"
            }
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
        auth_service.delete_admin_by_username(conn, username)

    return RedirectResponse(url="/admin/masters", status_code=303)


@router.post("/admin/masters/change-password")
async def change_password(
    request: Request,
    username: str = Form(...),
    new_password: str = Form(...),
    admin: str = Depends(is_admin)
):
    error = None

    if len(new_password) < 8:
        error = "New password must be at least 8 characters."
    elif not re.search(r"[A-Z]", new_password):
        error = "New password must contain an uppercase letter."

    if error:
        with engine.connect() as conn:
            admins = auth_service.get_all_admins_basic(conn)  # 👈 moved

        return templates.TemplateResponse("masters.html", {
            "request": request,
            "admins": admins,
            "error": error
        })

    hashed_password = pwd_context.hash(new_password)

    with engine.begin() as conn:
        auth_service.update_admin_password(conn, username, hashed_password)

    return RedirectResponse(url="/admin/masters", status_code=303)


if __name__ == "__main__":
    print("This is the auth router. It should be included in main.py and not run directly.")
    print("templates directory should be:", templates)