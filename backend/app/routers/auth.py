from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app import schemas, models
from app.database import get_db
from app.config import settings
from app.utils.auth import authenticate_user, create_access_token, get_password_hash
from app.utils.email import send_verification_email

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
async def register(
    user: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if user exists
    existing_user = db.query(models.User).filter(
        (models.User.email == user.email) |
        (models.User.username == user.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )

    # Hash password safely
    hashed_password = get_password_hash(user.password)

    new_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_verified=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email (background)
    background_tasks.add_task(send_verification_email, new_user.email)

    return new_user


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=401,
            detail="Email not verified"
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    # TODO: implement token decoding
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()

    if user:
        # TODO: send reset email
        pass

    return {"message": "If email exists, password reset instructions sent"}


@router.post("/reset-password/{token}")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    # TODO: implement reset logic
    return {"message": "Password reset successfully"}