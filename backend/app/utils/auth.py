from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ✅ Helper: safely truncate password
def safe_password(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", "ignore")


def verify_password(plain_password: str, hashed_password: str):
    password_bytes = plain_password.encode("utf-8")[:72]
    safe_password = password_bytes.decode("utf-8", errors="ignore")

    return pwd_context.verify(safe_password, hashed_password)


def get_password_hash(password: str):
    # 🔒 FORCE truncate safely (NO FAIL)
    password_bytes = password.encode("utf-8")[:72]
    safe_password = password_bytes.decode("utf-8", errors="ignore")

    print("DEBUG PASSWORD LENGTH:", len(password_bytes))  # 👈 ADD THIS

    return pwd_context.hash(safe_password)


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        print("❌ User not found")
        return None

    print("✅ User found:", user.email)

    if not verify_password(password, user.hashed_password):
        print("❌ Password mismatch")
        return None

    print("✅ Password correct")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


def require_role(required_role: str):
    def role_checker(
        current_user: models.User = Depends(get_current_active_user)
    ):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required"
            )
        return current_user

    return role_checker