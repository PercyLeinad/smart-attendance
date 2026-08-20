import re
from passlib.context import CryptContext
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from app.core.ui import templates
from app.core.database import engine
from app.core.session import is_admin
from app.services import auth as auth_service
import uuid
from fastapi.responses import RedirectResponse
from app.core.redis import redis_client
from app.core.session import SESSION_TIMEOUT
from app.services.auth import create_session,close_session

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
    session_id = request.cookies.get("session_id")

    if session_id:
        session_data = redis_client.hgetall(
            f"session:{session_id}"
        )

        if session_data:
            return RedirectResponse(
                url="/admin",
                status_code=303
            )

    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request}
    )

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    # Verify credentials
    with engine.connect() as conn:
        admin = auth_service.get_admin_password(conn, username)

    db_password = admin['password'] if admin else None

    if not db_password or not pwd_context.verify(password, db_password):
        return RedirectResponse(
            url="/login?msg=invalid_credentials",
            status_code=303
        )

    old_session_id = request.cookies.get("session_id")

    # Remove old Redis session
    if old_session_id:
        redis_client.delete(f"session:{old_session_id}")

        # Record old session as replaced
        with engine.begin() as conn:
            close_session(
                conn,
                old_session_id,
                "session_replaced"
            )

    # Create new session
    session_id = str(uuid.uuid4())

    ip_address = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")

    # Store active session in Redis
    redis_client.hset(
        f"session:{session_id}",
        mapping={
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
    )

    redis_client.expire(
        f"session:{session_id}",
        SESSION_TIMEOUT
    )

    # Store login audit record
    with engine.begin() as conn:
        create_session(
            conn,
            session_id,
            username,
            ip_address,
            user_agent
        )

    # Set cookie
    response = RedirectResponse(
        "/admin",
        status_code=303
    )

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return response

@router.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")

    response = RedirectResponse(
        url="/login",
        status_code=303
    )

    if session_id:
        # Remove active session from Redis
        redis_client.delete(f"session:{session_id}")

        # Record logout in database
        with engine.begin() as conn:
            close_session(
                conn,
                session_id,
                "logout"
            )

    # Remove browser cookie
    response.delete_cookie(
        key="session_id",
        path="/"
    )

    return response

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: str = Depends(is_admin)):
    # Fetch the missing data
    with engine.connect() as connection:
        stats = auth_service.get_dashboard_stats(connection)
        email = auth_service.get_admin_by_username(connection, admin)

    if email:
        admin_email = email['email']
    else:
        admin_email = "Unknown Email"
        
    response = templates.TemplateResponse(
        "admin_dashboard.html",
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

# Page to List Admins
@router.get("/admin/masters", response_class=HTMLResponse)
async def masters_page(request: Request, error: str = None, delete_error: str = None, admin: str = Depends(is_admin)):
    with engine.connect() as conn:
        admins = auth_service.list_all_admins(conn)
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request, 
        "admins": admins,
        "error": error,                 # Handles "Add Admin" modal errors
        "delete_error": delete_error,   # Handles page-level deletion errors
        "admin": admin                  # Pass the logged-in user down to the page context
    })

# Add New Admin
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
            "admin_users.html",
            {"request": request, "error": error, "username": username}
        )

    hashed_password = pwd_context.hash(password)

    try:
        with engine.begin() as conn:
            auth_service.add_new_admin(conn, username, email, hashed_password)

        return RedirectResponse(url="/admin/masters", status_code=303)

    except IntegrityError:
        return templates.TemplateResponse(
            "admin_users.html",
            {
                "request": request,
                "error": "Username or Email already exists",
                "username": username,
                "email": email
            }
        )

    except Exception:
        return templates.TemplateResponse(
            "admin_users.html",
            {
                "request": request,
                "error": "Something went wrong"
            }
        )

# Delete Admin
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

        return templates.TemplateResponse("admin_users.html", {
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