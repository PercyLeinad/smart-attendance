import re
from passlib.context import CryptContext
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.ui import templates
from app.core.database import engine
from app.core.session import is_admin
from app.services import auth as auth_service
from app.services import session as session_service

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
    # Check if a session cookie exists
    session_id = request.cookies.get("session_id")
    
    if session_id:
        with engine.connect() as conn:
            # Look up if it's a valid session in the DB
            user_session = session_service.get_session_by_id(conn, session_id)
            
        if user_session:
            # Admin is already validated! Don't let them log in again, send them to dashboard
            return RedirectResponse(url="/admin", status_code=303)

    # If no session or invalid session, show the login page normally
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # 1. Look up the admin credentials
    with engine.connect() as conn:
        admin = auth_service.get_admin_password(conn, username)

    db_password = admin['password'] if admin else None

    # 2. Check if the password matches
    if not db_password or not pwd_context.verify(password, db_password):
        return RedirectResponse(url="/login?msg=invalid_credentials", status_code=303)

    # 3. Gather environment metadata for security hardening
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # 4. Save session state to the database (using .begin() to automatically commit)
    # 🌟 NEW SECURITY LAYER: If the browser sent an old cookie, destroy it first!
    old_session_id = request.cookies.get("session_id")
    
    with engine.begin() as conn:
        if old_session_id:
            session_service.delete_user_session(conn, old_session_id)
            
        # This guarantees secrets.token_urlsafe(32) runs freshly for a new string
        session_token = session_service.create_user_session(
            conn=conn, 
            username=username, 
            ip_address=request.client.host if request.client else None, 
            user_agent=request.headers.get("user-agent")
        )

    # 5. Bind the random token to a secure, HTTP-Only browser cookie
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,        # Prevents JavaScript reading token (XSS protection)
        samesite="lax",       # Protects against CSRF attacks
        secure=False          # Set to True when running over HTTPS/SSL
    )
    return response


@router.get("/logout")
async def logout(request: Request):
    # 1. Retrieve the opaque session token from incoming cookies
    session_id = request.cookies.get("session_id")
    response = RedirectResponse(url="/login", status_code=303)
    
    if session_id:
        # 2. Drop the record completely from your MySQL database
        with engine.begin() as conn:
            session_service.delete_user_session(conn, session_id)
            
        # 3. Force the browser to clear the local cookie footprint
        response.delete_cookie(key="session_id", path="/")
        
    return response

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: str = Depends(is_admin)):
    # 1. Fetch the missing data
    with engine.connect() as connection:
        stats = auth_service.get_dashboard_stats(connection)
        email = auth_service.get_admin_by_username(connection, admin)

    if email:
        admin_email = email['email']
    else:
        admin_email = "Unknown Email"
        
    response = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "stats": stats,
            "current_admin": admin,
            "email": admin_email
        }
    )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

# 1. Page to List Admins
@router.get("/admin/masters", response_class=HTMLResponse)
async def masters_page(request: Request, error: str = None, delete_error: str = None, admin: str = Depends(is_admin)):
    with engine.connect() as conn:
        admins = auth_service.list_all_admins(conn)
    
    return templates.TemplateResponse("masters.html", {
        "request": request, 
        "admins": admins,
        "error": error,                 # Handles "Add Admin" modal errors
        "delete_error": delete_error,   # Handles page-level deletion errors
        "admin": admin                  # Pass the logged-in user down to the page context
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
                "error": "Username or Email already exists",
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
        # 🌟 Change: Use delete_error query param instead of error
        return RedirectResponse(
            url="/admin/masters?delete_error=You cannot delete your own account.",
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