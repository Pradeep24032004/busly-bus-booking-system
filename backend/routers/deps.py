
# routers/deps.py
from fastapi import Depends, HTTPException, Header
from typing import Optional
from auth import decode_token
from db import users_col
from bson import ObjectId

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Accepts Authorization header like: "Bearer <token>" or just the token.
    decode_token should return the 'sub' (user id string) or raise/return None.
    Returns the full user document from users_col.
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing auth")

    # Accept "Bearer <token>" or "<token>"
    scheme, _, token = authorization.partition(" ")
    if token == "":
        # header was just token
        token = scheme
    else:
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

    sub = decode_token(token)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")

    # try as ObjectId first, then fallback to string id field
    user = None
    try:
        if ObjectId.is_valid(sub):
            user = await users_col.find_one({"_id": ObjectId(sub)})
    except Exception:
        user = None

    if not user:
        # fallback: maybe _id is stored as string
        user = await users_col.find_one({"_id": sub})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def require_admin(user = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user
