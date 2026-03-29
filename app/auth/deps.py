from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import TokenData
from app.config import settings
from app.database import get_db
from app.models.org import AuditLog, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, role=payload.get("role"))
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(roles: list[str]):
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role} not permitted. Required: {roles}",
            )
        return current_user
    return _checker


async def require_unit_access(unit_id: str, db: AsyncSession, user: User) -> bool:
    from app.models.org import UnitAssignment
    result = await db.execute(
        select(UnitAssignment).where(
            UnitAssignment.user_id == user.id,
            UnitAssignment.unit_id == unit_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if assignment is None and user.role not in ("ADMIN", "MANAGER"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this unit")
    return True


async def check_ip_allowlist(request: Request, user: User, db: AsyncSession) -> None:
    """Stub: logs IP but does not block in MVP."""
    client_ip = request.client.host if request.client else "unknown"
    await log_audit_event(
        db=db,
        user_id=user.id,
        action="IP_CHECK",
        resource_type="access",
        resource_id=None,
        detail={"ip": client_ip},
        ip_address=client_ip,
    )


async def log_audit_event(
    db: AsyncSession,
    action: str,
    resource_type: str,
    user_id: str | None = None,
    resource_id: str | None = None,
    detail: dict[str, Any] | None = None,
    ip_address: str | None = None,
    device_fingerprint: str | None = None,
    is_break_glass: bool = False,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
        device_fingerprint=device_fingerprint,
        is_break_glass=is_break_glass,
    )
    db.add(log)
