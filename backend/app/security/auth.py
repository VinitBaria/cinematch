"""
CineMatch AI - JWT Authentication & Password Security
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from ..config import settings
from ..database import get_db


def hash_password(password: str) -> str:
    pwd_bytes = password[:72].encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain[:72].encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_current_user(request: Request):
    """Extract and validate JWT from Authorization header or cookie."""
    token = None

    # Check Authorization header first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # Fallback to cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("userId")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    db = get_db()
    user = db.users.find_one({"userId": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return {
        "userId": user["userId"],
        "email": user["email"],
        "name": user["name"],
    }


def get_optional_current_user(request: Request):
    """Extract and validate JWT, or return None if unauthenticated."""
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        return None

    payload = decode_token(token)
    if payload is None:
        return None

    user_id = payload.get("userId")
    if user_id is None:
        return None

    db = get_db()
    user = db.users.find_one({"userId": user_id})
    if not user:
        return None

    return {
        "userId": user["userId"],
        "email": user["email"],
        "name": user["name"],
    }

