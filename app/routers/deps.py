"""
Dependency helpers for FastAPI routes.

Provides:
  - get_current_user  — validates JWT and returns the User ORM object
  - require_roles     — factory that restricts access to specified roles
  - tenant_guard      — ensures the requested resource belongs to the caller's care home
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import User, UserRole

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def require_roles(*roles: UserRole):
    """Return a dependency that allows only users with the given roles."""

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires one of: {[r.value for r in roles]}",
            )
        return current_user

    return _check


def tenant_guard(resource_care_home_id: str, current_user: User) -> None:
    """Raise 403 if the resource belongs to a different care home."""
    if resource_care_home_id != current_user.care_home_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this resource is not permitted.",
        )
