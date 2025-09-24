from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# Utility for ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# User models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: str

class UserPublic(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    name: str
    email: EmailStr
    mobile: str
    balance: float
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

# Auth token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Route & bus
class RouteCreate(BaseModel):
    src_city: str
    dst_city: str

class BusCreate(BaseModel):
    route_id: str
    name: str
    start_time: datetime
    seats_count: int
    price_per_seat: float
    sales_open_time: Optional[datetime] = None
    status: Optional[str] = "published"

class BusPublic(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    route_id: str
    name: str
    start_time: datetime
    seats_count: int
    price_per_seat: float
    sales_open_time: Optional[datetime]
    status: str

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

# Seat selection and reservation
class SeatSelectionRequest(BaseModel):
    seat_numbers: List[str]

class ReservationResponse(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    user_id: str
    bus_id: str
    seat_numbers: List[str]
    total_price: float
    status: str
    expires_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

class PassengerInfo(BaseModel):
    seat_number: str
    name: str
    email: EmailStr
    mobile: str

class ConfirmRequest(BaseModel):
    passengers: List[PassengerInfo]
