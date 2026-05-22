import datetime
from fastapi import HTTPException, Request, status

SESSION_TIMEOUT = 900  # 15 minutes

def is_admin(request: Request) -> str:
    admin = request.session.get("admin")
    last_activity = request.session.get("last_activity")

    if not admin or not last_activity:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"}
        )

    last_activity = datetime.datetime.fromisoformat(last_activity)

    if datetime.datetime.now() - last_activity > datetime.timedelta(seconds=SESSION_TIMEOUT):
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login?msg=session_expired"}
        )

    request.session["last_activity"] = datetime.datetime.now().isoformat()
    return admin