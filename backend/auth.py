
# auth.py
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from config import settings  # expects JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = getattr(settings, "JWT_ALGORITHM", "HS256")
SECRET = getattr(settings, "JWT_SECRET", None)
if not SECRET:
    raise RuntimeError("JWT secret not configured (settings.JWT_SECRET)")

def hash_password(password: str) -> str:
    """Hash a password (bcrypt via passlib)."""
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hash."""
    if not hashed:
        return False
    return pwd_ctx.verify(plain, hashed)

def create_access_token(subject: str, expires_minutes: int = None) -> str:
    """
    Create a JWT with `sub` set to subject (usually user id).
    `expires_minutes` overrides the default ACCESS_TOKEN_EXPIRE_MINUTES from config.
    """
    if expires_minutes is None:
        expires_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
    now = datetime.utcnow()
    exp = now + timedelta(minutes=expires_minutes)
    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    # pyjwt may return bytes on some versions; ensure string
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_token(token: str):
    """
    Decode token and return the 'sub' (user id) when valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
