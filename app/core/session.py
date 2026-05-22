import datetime
from fastapi import HTTPException, Request, status
from app.core.database import engine
from app.services import session as session_service

SESSION_TIMEOUT = 900  # 15 minutes

def is_admin(request: Request) -> str:
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"}
        )

    # Note: Using .begin() automates rolling back if things fail, and commits upon exiting the block
    with engine.begin() as conn:
        user_session = session_service.get_session_by_id(conn, session_id)

        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": "/login"}
            )

        # Handle sliding time check explicitly without ORM helpers
        last_activity = user_session["last_activity"]
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        
        if now - last_activity > datetime.timedelta(seconds=SESSION_TIMEOUT):
            session_service.delete_user_session(conn, session_id)
            
            response = HTTPException(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": "/login?msg=session_expired"}
            )
            response.headers["Set-Cookie"] = "session_id=; Path=/; Max-Age=0;"
            raise response

        # Everything checks out, update the sliding timeout activity log
        session_service.update_session_activity(conn, session_id)
        
        return user_session["username"]