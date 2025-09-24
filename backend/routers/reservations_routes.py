

# routers/reservations.py
from fastapi import APIRouter, Depends, HTTPException, status
from routers.deps import get_current_user
from models import SeatSelectionRequest, ConfirmRequest
from db import reservations_col, seats_col, bookings_col, passengers_col, transactions_col, users_col, buses_col
from seat_lock_manager import SeatLockManager
from config import settings
from datetime import datetime, timedelta
from bson import ObjectId
from typing import List
# routers/reservations.py (only the confirm endpoint shown — keep rest unchanged)
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
# ... other imports unchanged ...
from utils.email_utils import send_email_sync   # new import

router = APIRouter(prefix="/reservations", tags=["reservations"])
lock_manager = SeatLockManager()


def _ensure_valid_bus_id(bus_id: str):
    if not ObjectId.is_valid(bus_id):
        raise HTTPException(status_code=400, detail="Invalid bus id")
    return ObjectId(bus_id)


@router.post("/select/{bus_id}", status_code=201)
async def select_seats(bus_id: str, payload: SeatSelectionRequest, user=Depends(get_current_user)):
    """
    Reserve seats temporarily (creates a reservation with status='pending').
    Uses in-memory non-blocking locks plus marks seats 'reserved' in DB with reserved_by_reservation_id set to the
    reservation id (string). Returns reservation summary.
    """
    # validate bus id
    bus_oid = _ensure_valid_bus_id(bus_id)

    seats = payload.seat_numbers or []
    if not seats:
        raise HTTPException(status_code=400, detail="No seats requested")

    # quick DB check that seats exist for this bus
    q = {"bus_id": bus_oid, "seat_number": {"$in": seats}}
    seat_docs = await seats_col.find(q).to_list(length=len(seats))
    if len(seat_docs) != len(seats):
        raise HTTPException(status_code=404, detail="One or more seats not found")

    # check if any seat already booked
    already_booked = [s["seat_number"] for s in seat_docs if s.get("status") == "booked"]
    if already_booked:
        raise HTTPException(status_code=409, detail={"conflicting_seats": already_booked})

    # reserve via in-memory non-blocking locks
    reservation_oid = ObjectId()
    reservation_id_str = str(reservation_oid)
    ok, conflicts = lock_manager.try_acquire_many(bus_id, seats, reservation_id_str)
    if not ok:
        # conflicts: release any local locks just in case and return conflict
        lock_manager.release_many(bus_id, seats, reservation_id_str)
        raise HTTPException(status_code=409, detail={"conflicting_seats": conflicts})

    # calculate price
    bus = await buses_col.find_one({"_id": bus_oid})
    if not bus:
        # release locks and raise
        lock_manager.release_many(bus_id, seats, reservation_id_str)
        raise HTTPException(status_code=404, detail="Bus not found")
    price = float(bus.get("price_per_seat", 0.0)) or 0.0
    total_price = price * len(seats)

    expires_at = datetime.utcnow() + timedelta(seconds=getattr(settings, "RESERVATION_TTL_SECONDS", 300))
    # reservation: store user_id as string for easy comparison (assumes get_current_user returns string id at user["_id"])
    user_id_str = str(user.get("_id")) if user and user.get("_id") is not None else None

    reservation_doc = {
        "_id": reservation_oid,
        "user_id": user_id_str,
        "bus_id": str(bus_oid),          # store bus id as string inside reservation
        "seat_numbers": seats,
        "total_price": total_price,
        "status": "pending",
        "expires_at": expires_at,
        "created_at": datetime.utcnow()
    }

    # mark seats reserved in DB (store reserved_by_reservation_id as string)
    update_result = await seats_col.update_many(
        {"bus_id": bus_oid, "seat_number": {"$in": seats}, "status": "available"},
        {"$set": {"status": "reserved", "reserved_by_reservation_id": reservation_id_str}}
    )

    if update_result.modified_count != len(seats):
        # Race: some seats changed after we inspected. Roll back locks and any partial updates.
        # Revert any seats that we reserved
        await seats_col.update_many(
            {"bus_id": bus_oid, "seat_number": {"$in": seats}, "reserved_by_reservation_id": reservation_id_str},
            {"$set": {"status": "available", "reserved_by_reservation_id": None}}
        )
        lock_manager.release_many(bus_id, seats, reservation_id_str)
        raise HTTPException(status_code=409, detail="One or more seats became unavailable while reserving")

    # insert reservation
    await reservations_col.insert_one(reservation_doc)

    # return reservation (normalize ids to strings for client)
    res = {
        "id": reservation_id_str,
        "_id": reservation_id_str,
        "user_id": user_id_str,
        "bus_id": str(bus_oid),
        "seat_numbers": seats,
        "total_price": total_price,
        "expires_at": expires_at.isoformat()
    }
    return res


# @router.post("/confirm/{reservation_id}", status_code=201)
# async def confirm(reservation_id: str, payload: ConfirmRequest, user=Depends(get_current_user)):
#     """
#     Confirm a pending reservation: charge user balance, create booking, persist passenger info, create transaction,
#     finalize seats to 'booked', update reservation status to 'confirmed', release locks.
#     """
#     # validate reservation id
#     if not ObjectId.is_valid(reservation_id):
#         raise HTTPException(status_code=400, detail="Invalid reservation id")

#     reservation_oid = ObjectId(reservation_id)
#     reservation = await reservations_col.find_one({"_id": reservation_oid})
#     if not reservation:
#         raise HTTPException(status_code=404, detail="Reservation not found")

#     if reservation.get("status") != "pending":
#         raise HTTPException(status_code=400, detail="Reservation not pending")

#     # check ownership: we store user_id as string (see select_seats)
#     user_id_str = str(user.get("_id")) if user and user.get("_id") is not None else None
#     if reservation.get("user_id") != user_id_str:
#         raise HTTPException(status_code=403, detail="Not your reservation")

#     # expired?
#     if reservation.get("expires_at") and reservation["expires_at"] <= datetime.utcnow():
#         # cleanup
#         await _cancel_reservation(reservation)
#         raise HTTPException(status_code=400, detail="Reservation expired")

#     seats = reservation.get("seat_numbers", [])
#     total_price = float(reservation.get("total_price", 0.0))

#     # check user balance (we assume users_col stores numeric "balance")
#     user_doc = await users_col.find_one({"_id": ObjectId(user_id_str)}) if ObjectId.is_valid(user_id_str) else await users_col.find_one({"_id": user_id_str})
#     if not user_doc:
#         # unexpected - but handle
#         await _cancel_reservation(reservation)
#         raise HTTPException(status_code=404, detail="User account not found")

#     user_balance = float(user_doc.get("balance", 0.0))

#     if user_balance < total_price:
#         # release seats and locks
#         await _cancel_reservation(reservation)
#         # return structured error so frontend can show required vs available
#         raise HTTPException(status_code=402, detail={"required": total_price, "available": user_balance})

#     # Attempt to atomically set seats -> booked only if they are reserved by this reservation id
#     bus_oid = ObjectId(reservation["bus_id"]) if ObjectId.is_valid(reservation["bus_id"]) else None
#     update_result = await seats_col.update_many(
#         {
#             "bus_id": bus_oid,
#             "seat_number": {"$in": seats},
#             "status": "reserved",
#             "reserved_by_reservation_id": reservation_id
#         },
#         {"$set": {"status": "booked", "booked_by_booking_id": str(ObjectId())}}
#     )

#     if update_result.modified_count != len(seats):
#         # conflict: some seat changed or not reserved properly
#         await _cancel_reservation(reservation)
#         raise HTTPException(status_code=409, detail="Seat state conflict during booking")

#     # Deduct user balance
#     new_balance = user_balance - total_price
#     await users_col.update_one({"_id": user_doc["_id"]}, {"$set": {"balance": new_balance}})

#     # Create booking
#     booking_doc = {
#         "reservation_id": reservation_oid,
#         "user_id": user_id_str,
#         "bus_id": reservation["bus_id"],
#         "total_price": total_price,
#         "created_at": datetime.utcnow()
#     }
#     booking_res = await bookings_col.insert_one(booking_doc)
#     booking_id = booking_res.inserted_id

#     # Insert passengers
#     passengers_to_insert = []
#     for p in payload.passengers:
#         passengers_to_insert.append({
#             "booking_id": booking_id,
#             "seat_number": p.seat_number,
#             "passenger_name": p.name,
#             "passenger_email": p.email,
#             "passenger_mobile": p.mobile,
#             "created_at": datetime.utcnow()
#         })
#     if passengers_to_insert:
#         await passengers_col.insert_many(passengers_to_insert)

#     # Create transaction record (held)
#     tx = {
#         "from_user_id": user_id_str,
#         "to_admin": True,
#         "amount": total_price,
#         "status": "held",
#         "description": f"Booking {str(booking_id)} for bus {reservation['bus_id']}",
#         "timestamp": datetime.utcnow()
#     }
#     await transactions_col.insert_one(tx)

#     # Mark reservation confirmed
#     await reservations_col.update_one({"_id": reservation_oid}, {"$set": {"status": "confirmed", "booking_id": booking_id}})

#     # Release locks for these seats
#     lock_manager.release_many(reservation["bus_id"], seats, reservation_id)

#     return {"booking_id": str(booking_id)}

# routers/reservations.py (only the confirm endpoint shown — keep rest unchanged)
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
# ... other imports unchanged ...
from utils.email_utils import send_email_sync   # new import

# ... other code unchanged ...

@router.post("/confirm/{reservation_id}", status_code=201)
async def confirm(reservation_id: str, payload: ConfirmRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    """
    Confirm a pending reservation: charge user balance, create booking, persist passenger info, create transaction,
    finalize seats to 'booked', update reservation status to 'confirmed', release locks.
    Also: enqueue an email to the user with the ticket/confirmation details.
    """
    # validate reservation id
    if not ObjectId.is_valid(reservation_id):
        raise HTTPException(status_code=400, detail="Invalid reservation id")

    reservation_oid = ObjectId(reservation_id)
    reservation = await reservations_col.find_one({"_id": reservation_oid})
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Reservation not pending")

    # check ownership: we store user_id as string (see select_seats)
    user_id_str = str(user.get("_id")) if user and user.get("_id") is not None else None
    if reservation.get("user_id") != user_id_str:
        raise HTTPException(status_code=403, detail="Not your reservation")

    # expired?
    if reservation.get("expires_at") and reservation["expires_at"] <= datetime.utcnow():
        # cleanup
        await _cancel_reservation(reservation)
        raise HTTPException(status_code=400, detail="Reservation expired")

    seats = reservation.get("seat_numbers", [])
    total_price = float(reservation.get("total_price", 0.0))

    # check user balance (we assume users_col stores numeric "balance")
    user_doc = await users_col.find_one({"_id": ObjectId(user_id_str)}) if ObjectId.is_valid(user_id_str) else await users_col.find_one({"_id": user_id_str})
    if not user_doc:
        # unexpected - but handle
        await _cancel_reservation(reservation)
        raise HTTPException(status_code=404, detail="User account not found")

    user_balance = float(user_doc.get("balance", 0.0))

    if user_balance < total_price:
        # release seats and locks
        await _cancel_reservation(reservation)
        # return structured error so frontend can show required vs available
        raise HTTPException(status_code=402, detail={"required": total_price, "available": user_balance})

    # Attempt to atomically set seats -> booked only if they are reserved by this reservation id
    bus_oid = ObjectId(reservation["bus_id"]) if ObjectId.is_valid(reservation["bus_id"]) else None
    update_result = await seats_col.update_many(
        {
            "bus_id": bus_oid,
            "seat_number": {"$in": seats},
            "status": "reserved",
            "reserved_by_reservation_id": reservation_id
        },
        {"$set": {"status": "booked", "booked_by_booking_id": str(ObjectId())}}
    )

    if update_result.modified_count != len(seats):
        # conflict: some seat changed or not reserved properly
        await _cancel_reservation(reservation)
        raise HTTPException(status_code=409, detail="Seat state conflict during booking")

    # Deduct user balance
    new_balance = user_balance - total_price
    await users_col.update_one({"_id": user_doc["_id"]}, {"$set": {"balance": new_balance}})

    # Create booking
    booking_doc = {
        "reservation_id": reservation_oid,
        "user_id": user_id_str,
        "bus_id": reservation["bus_id"],
        "total_price": total_price,
        "created_at": datetime.utcnow()
    }
    booking_res = await bookings_col.insert_one(booking_doc)
    booking_id = booking_res.inserted_id

    # Insert passengers
    passengers_to_insert = []
    for p in payload.passengers:
        passengers_to_insert.append({
            "booking_id": booking_id,
            "seat_number": p.seat_number,
            "passenger_name": p.name,
            "passenger_email": p.email,
            "passenger_mobile": p.mobile,
            "created_at": datetime.utcnow()
        })
    if passengers_to_insert:
        await passengers_col.insert_many(passengers_to_insert)

    # Create transaction record (held)
    tx = {
        "from_user_id": user_id_str,
        "to_admin": True,
        "amount": total_price,
        "status": "held",
        "description": f"Booking {str(booking_id)} for bus {reservation['bus_id']}",
        "timestamp": datetime.utcnow()
    }
    await transactions_col.insert_one(tx)

    # Mark reservation confirmed
    await reservations_col.update_one({"_id": reservation_oid}, {"$set": {"status": "confirmed", "booking_id": booking_id}})

    # Release locks for these seats
    lock_manager.release_many(reservation["bus_id"], seats, reservation_id)

    # --- NEW: enqueue background email to user (non-blocking) ---
    try:
        # prepare ticket/email content
        ticket_id = str(booking_id)
        # gather bus info if available (for route/time)
        bus_doc = await buses_col.find_one({"_id": ObjectId(reservation["bus_id"])}) if ObjectId.is_valid(reservation["bus_id"]) else await buses_col.find_one({"_id": reservation["bus_id"]})
        route_summary = ""
        if bus_doc:
            # if you store route fields, adapt accordingly
            src = bus_doc.get("src_city") or bus_doc.get("route_src") or ""
            dst = bus_doc.get("dst_city") or bus_doc.get("route_dst") or ""
            start_time = bus_doc.get("start_time")
            start_time_str = start_time.isoformat() if start_time else ""
            route_summary = f"{src} → {dst} at {start_time_str}"
        else:
            route_summary = f"Bus {reservation.get('bus_id')}"

        # passengers summary
        passengers_lines = []
        for p in payload.passengers:
            passengers_lines.append(f"{p.name} (seat {p.seat_number}) - {p.email} / {p.mobile}")
        passengers_text = "\n".join(passengers_lines) if passengers_lines else "N/A"

        # email subject & body
        user_email = user_doc.get("email")
        subject = f"Booking confirmation — Ticket #{ticket_id}"
        body = f"""Hello {user_doc.get('name') or ''},

Your booking is confirmed.

Ticket ID: {ticket_id}
Route & Time: {route_summary}
Seats: {', '.join(seats)}
Total paid: ₹{total_price:.2f}
Booking created at: {datetime.utcnow().isoformat()}

Passengers:
{passengers_text}

If you have any questions, reply to this email.

Thank you,
BusBooking Team
"""
        # schedule background send
        background_tasks.add_task(send_email_sync, user_email, subject, body)
    except Exception as e:
        # don't break the flow if email fails: log and continue
        import logging
        logging.getLogger("uvicorn.error").exception("Failed to schedule booking email: %s", e)

    return {"booking_id": str(booking_id)}

async def _cancel_reservation(reservation):
    """
    Cancel a pending reservation - mark seats available and release locks, set reservation status to cancelled.
    Important: reserved_by_reservation_id in seats is stored as string.
    """
    # get reservation id string
    res_id_str = str(reservation["_id"])
    # bus oid to match seat bus_id (seats have bus_id as ObjectId)
    bus_oid = ObjectId(reservation["bus_id"]) if ObjectId.is_valid(reservation["bus_id"]) else reservation["bus_id"]

    # only revert seats reserved by this reservation id
    await seats_col.update_many(
        {"bus_id": bus_oid, "seat_number": {"$in": reservation["seat_numbers"]}, "reserved_by_reservation_id": res_id_str},
        {"$set": {"status": "available", "reserved_by_reservation_id": None}}
    )

    await reservations_col.update_one({"_id": reservation["_id"]}, {"$set": {"status": "cancelled"}})

    # release in-memory locks (reservation bus_id stored as string)
    lock_manager.release_many(str(reservation["bus_id"]), reservation["seat_numbers"], res_id_str)


@router.post("/cancel/{reservation_id}")
async def cancel_reservation(reservation_id: str, user=Depends(get_current_user)):
    if not ObjectId.is_valid(reservation_id):
        raise HTTPException(status_code=400, detail="Invalid reservation id")
    reservation = await reservations_col.find_one({"_id": ObjectId(reservation_id)})
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    user_id_str = str(user.get("_id"))
    if reservation.get("user_id") != user_id_str:
        raise HTTPException(status_code=403, detail="Not your reservation")
    await _cancel_reservation(reservation)
    return {"status": "cancelled"}
