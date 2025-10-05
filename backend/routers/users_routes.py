

# routers/users_routes.py
from fastapi import APIRouter, Depends, HTTPException
from routers.deps import get_current_user
from db import users_col, bookings_col, topup_requests_col, buses_col, routes_col, passengers_col, seats_col, transactions_col
from datetime import datetime
from bson import ObjectId
from typing import Any, Dict, Optional, List

router = APIRouter(prefix="/users", tags=["users"])

def _to_objectid_if_possible(val: Any) -> Optional[ObjectId]:
    try:
        if isinstance(val, ObjectId):
            return val
        if isinstance(val, str) and ObjectId.is_valid(val):
            return ObjectId(val)
    except Exception:
        pass
    return None

@router.get("/me")
async def me(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role"),
        "balance": float(user.get("balance", 0.0)),
        "mobile": user.get("mobile"),
        "created_at": user.get("created_at")
    }

@router.get("/me/bookings")
async def my_bookings(user=Depends(get_current_user)):
    """
    Return bookings for current user, most recent first.
    Each booking includes route, bus_start_time, seats and passenger list.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    uid = user.get("_id")
    q_or = []
    oid = _to_objectid_if_possible(uid)
    if oid:
        q_or.append({"user_id": oid})
    q_or.append({"user_id": str(uid)})

    cursor = bookings_col.find({"$or": q_or}).sort("created_at", -1).limit(100)
    out: List[Dict[str, Any]] = []
    async for b in cursor:
        b_id = b.get("_id")
        reservation_id = b.get("reservation_id")
        bus_id = b.get("bus_id")
        total_price = float(b.get("total_price", 0.0))
        status = b.get("status")
        created_at = b.get("created_at")

        b_id_str = str(b_id) if b_id is not None else None
        reservation_id_str = str(reservation_id) if reservation_id is not None else None
        bus_id_str = None
        if isinstance(bus_id, ObjectId):
            bus_id_str = str(bus_id)
        elif isinstance(bus_id, str):
            bus_id_str = bus_id
        else:
            bus_id_str = str(bus_id) if bus_id is not None else None

        # Lookup bus
        bus_doc = None
        try:
            if bus_id_str and ObjectId.is_valid(bus_id_str):
                bus_doc = await buses_col.find_one({"_id": ObjectId(bus_id_str)})
        except Exception:
            bus_doc = None
        if not bus_doc and bus_id_str:
            bus_doc = await buses_col.find_one({"_id": bus_id_str})

        route_info = None
        bus_start_time = None
        if bus_doc:
            src = bus_doc.get("src_city") or bus_doc.get("route_src") or None
            dst = bus_doc.get("dst_city") or bus_doc.get("route_dst") or None
            route_id = bus_doc.get("route_id")
            if route_id and (not src or not dst):
                try:
                    if ObjectId.is_valid(route_id):
                        rdoc = await routes_col.find_one({"_id": ObjectId(route_id)})
                    else:
                        rdoc = await routes_col.find_one({"_id": route_id})
                except Exception:
                    rdoc = None
                if rdoc:
                    src = rdoc.get("src_city") or rdoc.get("src") or rdoc.get("source") or src
                    dst = rdoc.get("dst_city") or rdoc.get("dst") or rdoc.get("destination") or dst

            start_time = bus_doc.get("start_time")
            if isinstance(start_time, datetime):
                bus_start_time = start_time.isoformat()
            elif isinstance(start_time, str):
                bus_start_time = start_time
            else:
                bus_start_time = None

            if src or dst:
                route_info = {"src": src or "", "dst": dst or ""}

        # passengers & seats
        seats_list: List[str] = []
        passengers_list: List[Dict[str, Any]] = []
        try:
            booking_objid = None
            if b_id is not None and isinstance(b_id, ObjectId):
                booking_objid = b_id
            elif b_id_str and ObjectId.is_valid(b_id_str):
                booking_objid = ObjectId(b_id_str)

            if booking_objid:
                p_cursor = passengers_col.find({"booking_id": booking_objid})
            else:
                p_cursor = passengers_col.find({"booking_id": b_id_str})
            async for p in p_cursor:
                seat_num = p.get("seat_number")
                if seat_num:
                    seats_list.append(seat_num)
                passengers_list.append({
                    "seat_number": p.get("seat_number"),
                    "name": p.get("passenger_name") or p.get("name"),
                    "email": p.get("passenger_email") or p.get("email"),
                    "mobile": p.get("passenger_mobile") or p.get("mobile")
                })
        except Exception:
            seats_list = []
            passengers_list = []

        out.append({
            "id": b_id_str,
            "reservation_id": reservation_id_str,
            "bus_id": bus_id_str,
            "total_price": total_price,
            "status": status,
            "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
            "route": route_info,
            "bus_start_time": bus_start_time,
            "seats": seats_list,
            "passengers": passengers_list
        })

    return {"bookings": out}

@router.post("/request-topup", status_code=201)
async def request_topup(payload: Dict[str, Any], user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    amount = payload.get("amount")
    note = payload.get("note", "")
    try:
        amount = float(amount)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid amount")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0")
    uid = user.get("_id")
    oid = _to_objectid_if_possible(uid) or uid
    req_doc = {
        "user_id": oid,
        "amount": amount,
        "note": note,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "approved_by": None,
        "approved_at": None,
        "rejected_reason": None
    }
    res = await topup_requests_col.insert_one(req_doc)
    return {"id": str(res.inserted_id), "status": "pending", "amount": amount}

@router.post("/change-password")
async def change_password(payload: Dict[str, Any], user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    old = payload.get("old_password")
    new = payload.get("new_password")
    if not old or not new or len(new) < 6:
        raise HTTPException(status_code=400, detail="Invalid password data")
    stored_hash = user.get("password_hash") or user.get("password")
    if stored_hash is None:
        raise HTTPException(status_code=400, detail="Password not set for user")
    from auth import verify_password, hash_password
    if not verify_password(old, stored_hash):
        raise HTTPException(status_code=403, detail="Old password does not match")
    new_hash = hash_password(new)
    await users_col.update_one({"_id": user["_id"]}, {"$set": {"password_hash": new_hash}})
    return {"status": "ok", "message": "Password updated"}

@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, user=Depends(get_current_user)):
    """
    Cancel a booking belonging to the current user.
    Refunds balance, frees seats, inserts refund tx, marks booking cancelled.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    # find booking
    booking_doc = None
    try:
        if ObjectId.is_valid(booking_id):
            booking_doc = await bookings_col.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        booking_doc = None
    if not booking_doc:
        booking_doc = await bookings_col.find_one({"_id": booking_id})
    if not booking_doc:
        raise HTTPException(status_code=404, detail="Booking not found")

    # ownership check
    user_id_str = str(user.get("_id"))
    b_user_id = booking_doc.get("user_id")
    b_user_id_str = str(b_user_id) if b_user_id is not None else None
    if b_user_id_str != user_id_str:
        raise HTTPException(status_code=403, detail="Not your booking")

    # prevent double cancel
    if booking_doc.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    # gather seats from passengers_col
    seats = []
    try:
        p_query = {}
        try:
            if isinstance(booking_doc.get("_id"), ObjectId):
                p_query = {"booking_id": booking_doc["_id"]}
            elif ObjectId.is_valid(str(booking_doc.get("_id"))):
                p_query = {"booking_id": ObjectId(str(booking_doc.get("_id")))}
            else:
                p_query = {"booking_id": str(booking_doc.get("_id"))}
        except Exception:
            p_query = {"booking_id": str(booking_doc.get("_id"))}

        cursor = passengers_col.find(p_query)
        async for p in cursor:
            s = p.get("seat_number")
            if s:
                seats.append(s)
    except Exception:
        seats = []

    # free seats (only if currently booked)
    bus_id = booking_doc.get("bus_id")
    bus_oid = _to_objectid_if_possible(bus_id)
    seat_filter = {
        "seat_number": {"$in": seats}
    }
    if bus_oid:
        seat_filter["bus_id"] = bus_oid
    else:
        seat_filter["bus_id"] = bus_id

    if seats:
        await seats_col.update_many(
            {**seat_filter, "status": "booked"},
            {"$set": {"status": "available"}, "$unset": {"booked_by_booking_id": "", "reserved_by_reservation_id": ""}}
        )

    # refund
    total_price = float(booking_doc.get("total_price", 0.0))
    user_q = {"_id": ObjectId(user_id_str)} if ObjectId.is_valid(user_id_str) else {"_id": user_id_str}
    user_doc = await users_col.find_one(user_q)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User account not found")

    new_balance = float(user_doc.get("balance", 0.0)) + total_price
    await users_col.update_one(user_q, {"$set": {"balance": new_balance}})

    # transaction record
    tx = {
        "from_user_id": None,
        "to_user_id": str(user_doc["_id"]),
        "amount": total_price,
        "status": "settled",
        "type": "refund",
        "description": f"Refund for cancelled booking {str(booking_doc.get('_id'))}",
        "timestamp": datetime.utcnow()
    }
    await transactions_col.insert_one(tx)

    # mark booking cancelled
    await bookings_col.update_one({"_id": booking_doc["_id"]}, {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}})

    return {"status": "cancelled", "booking_id": str(booking_doc["_id"]), "refunded": total_price, "new_balance": new_balance}

