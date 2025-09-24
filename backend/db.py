from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

# Helpful collection references
users_col = db["users"]
routes_col = db["routes"]
buses_col = db["buses"]
seats_col = db["seats"]
reservations_col = db["reservations"]
bookings_col = db["bookings"]
passengers_col = db["passengers"]
transactions_col = db["transactions"]
topup_requests_col = db["topup_requests"]
