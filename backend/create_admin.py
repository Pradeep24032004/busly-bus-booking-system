# create_admin.py
from pymongo import MongoClient
from passlib.context import CryptContext
from datetime import datetime
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "bus_booking")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db["users"]

email = "admin@yourdomain.com"
password = "AdminPass123!"   # change to a secure password

hashed = pwd_context.hash(password)
doc = {
    "name": "Site Admin",
    "email": email,
    "password_hash": hashed,
    "mobile": "9999999999",
    "balance": 0.0,
    "created_at": datetime.utcnow(),
    "role": "admin",
}

res = users.insert_one(doc)
print("Created admin id:", res.inserted_id)
print("Login at frontend with:", email, password)
