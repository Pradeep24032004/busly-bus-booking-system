# from pydantic import BaseSettings

# class Settings(BaseSettings):
#     MONGO_URI: str = "mongodb://localhost:27017"
#     DB_NAME: str = "bus_booking"
#     JWT_SECRET: str = "e7f3c9a1b2d4e5f67890ab12c3d4e5f6a7b8c9d0e1f23456789abcdef01234567"
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
#     RESERVATION_TTL_SECONDS: int = 10 * 60  # 10 minutes
#     INITIAL_BALANCE: float = 1000.0

#     class Config:
#         env_file = ".env"

# settings = Settings()

# config.py (add these fields to your existing Settings class)
from pydantic import BaseSettings
from typing import Optional  # 👈 add this

class Settings(BaseSettings):
    # ... existing fields ...
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "bus_booking"
    JWT_SECRET: str = "..."  # your secret
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    RESERVATION_TTL_SECONDS: int = 10 * 60
    INITIAL_BALANCE: float = 1000.0

    # --- SMTP settings for outgoing email ---
    SMTP_HOST: Optional[str] = None       # e.g. "smtp.gmail.com"
    SMTP_PORT: Optional[int] = None       # e.g. 465 for SSL or 587 for TLS
    SMTP_USER: Optional[str] = None       # SMTP username
    SMTP_PASSWORD: Optional[str] = None   # SMTP password or app password
    SMTP_FROM: Optional[str] = None       # default FROM address, e.g. "no-reply@mydomain.com"
    SMTP_USE_SSL: bool = True             # true => use SMTP_SSL (port 465), false => starttls (587)

    class Config:
        env_file = ".env"

settings = Settings()
