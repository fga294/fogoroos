"""HTTP Basic authentication for coach/admin routes."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import get_settings

security = HTTPBasic(auto_error=False)


def verify_admin(credentials: Annotated[HTTPBasicCredentials | None, Depends(security)]) -> str:
    """
    Require valid Basic credentials. Returns the authenticated username.
    Uses constant-time comparison for the password.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic realm=\"U14 Admin\""},
        )
    settings = get_settings()
    user_ok = secrets.compare_digest(credentials.username.encode(), settings.admin_username.encode())
    pass_ok = secrets.compare_digest(credentials.password.encode(), settings.admin_password.encode())
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic realm=\"U14 Admin\""},
        )
    return credentials.username
