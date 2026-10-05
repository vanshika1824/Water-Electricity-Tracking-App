from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user, store securely in PostgreSQL, and return JWT token."""
    # Check for existing email (case-insensitive check)
    existing_user = db.query(User).filter(User.email.ilike(user_in.email.strip())).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Hash password securely
    hashed_pwd = hash_password(user_in.password)

    new_user = User(
        full_name=user_in.full_name.strip(),
        email=user_in.email.strip().lower(),
        hashed_password=hashed_pwd,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate token
    token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

    user_resp = UserResponse(
        id=new_user.id,
        full_name=new_user.full_name,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        has_profile=False
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    """Authenticate credentials against PostgreSQL and return JWT token."""
    user = db.query(User).filter(User.email.ilike(login_in.email.strip())).first()

    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

    token = create_access_token(data={"sub": str(user.id), "email": user.email})

    has_profile = user.profile is not None
    user_resp = UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        has_profile=has_profile
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile information of the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        has_profile=current_user.profile is not None
    )
