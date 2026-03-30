"""Authentication router — login and token refresh."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            User.email == payload.email,
            User.care_home_id == payload.care_home_id,
            User.is_active.is_(True),
        )
        .first()
    )
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(
        {
            "sub": user.id,
            "role": user.role.value,
            "care_home_id": user.care_home_id,
        }
    )
    return TokenResponse(access_token=token)
