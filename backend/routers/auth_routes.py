
# routers/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from models import UserCreate, Token  # Token from your models.py
from pydantic import BaseModel, EmailStr
from db import users_col
from auth import hash_password, verify_password, create_access_token
from datetime import datetime
from config import settings
from routers.deps import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])

class SignInPayload(BaseModel):
    email: EmailStr
    password: str

@router.get("/me")
async def auth_me(user = Depends(get_current_user)):
    # user is full user doc returned by deps
    return {
        "id": str(user.get("_id")),
        "name": user.get("name"),
        "email": user.get("email"),
        "mobile": user.get("mobile"),
        "balance": float(user.get("balance", 0.0)),
        "role": user.get("role", "user"),
        "created_at": user.get("created_at")
    }

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate):
    existing = await users_col.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(payload.password)
    doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": hashed,
        "mobile": payload.mobile,
        "balance": settings.INITIAL_BALANCE,
        "created_at": datetime.utcnow(),
        "role": "user"
    }
    res = await users_col.insert_one(doc)
    token = create_access_token(str(res.inserted_id))
    return {"access_token": token, "token_type": "bearer"}

@router.post("/signin", response_model=Token)
async def signin(payload: SignInPayload):
    user = await users_col.find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(payload.password, user.get("password_hash")):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(str(user["_id"]))
    return {"access_token": token, "token_type": "bearer"}
