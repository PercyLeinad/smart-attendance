from fastapi import HTTPException, Request, status
from app.core.redis import redis_client

SESSION_TIMEOUT = 900


def is_admin(request: Request) -> str:
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"}
        )

    session_key = f"session:{session_id}"

    session_data = redis_client.hgetall(session_key)

    # Session missing or expired
    if not session_data:
        exc = HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login?msg=session_expired"}
        )

        exc.headers["Set-Cookie"] = (
            "session_id=; Path=/; Max-Age=0;"
        )

        raise exc

    # Sliding expiration
    redis_client.expire(
        session_key,
        SESSION_TIMEOUT
    )

    return session_data["username"]