"""
CineMatch AI - Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Response, Depends, status
from datetime import datetime, timezone
from ..database import get_db
from ..security.auth import hash_password, verify_password, create_access_token, get_current_user
from ..schemas.schemas import RegisterRequest, LoginRequest, AuthResponse, UserProfile

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

APP_USER_ID_OFFSET = 1_000_000


def _get_next_user_id() -> int:
    db = get_db()
    last = db.users.find_one(sort=[("userId", -1)])
    if last:
        return max(last["userId"] + 1, APP_USER_ID_OFFSET)
    return APP_USER_ID_OFFSET


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    db = get_db()

    if db.users.find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = _get_next_user_id()
    now = datetime.now(timezone.utc).isoformat()

    user_doc = {
        "userId": user_id,
        "name": req.name,
        "email": req.email,
        "passwordHash": hash_password(req.password),
        "createdAt": now,
        "updatedAt": now,
    }
    db.users.insert_one(user_doc)

    token = create_access_token({"userId": user_id, "email": req.email})

    return AuthResponse(userId=user_id, name=req.name, email=req.email, token=token)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    db = get_db()
    user = db.users.find_one({"email": req.email})

    pwd_hash = user.get("passwordHash") or user.get("hashedPassword")
    if not user or not pwd_hash or not verify_password(req.password, pwd_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")


    token = create_access_token({"userId": user["userId"], "email": user["email"]})

    return AuthResponse(
        userId=user["userId"], name=user["name"], email=user["email"], token=token
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserProfile)
def get_me(current_user=Depends(get_current_user)):
    db = get_db()
    rating_count = db.ratings.count_documents({"userId": current_user["userId"]})
    user = db.users.find_one({"userId": current_user["userId"]})

    return UserProfile(
        userId=current_user["userId"],
        name=current_user["name"],
        email=current_user["email"],
        ratingCount=rating_count,
        createdAt=user.get("createdAt") if user else None,
    )
