
# routers/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from routers.deps import require_admin
from db import routes_col, buses_col, seats_col, bookings_col, transactions_col
from models import RouteCreate, BusCreate
from datetime import datetime, timedelta, time
from bson import ObjectId
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _generate_40_seats(bus_obj_id: ObjectId) -> List[Dict[str, Any]]:
    seats_docs = []
    seat_counter = 1
    ROWS = 10
    for row in range(1, ROWS + 1):
        for col in (1, 2):
            seats_docs.append({
                "bus_id": bus_obj_id,
                "seat_number": str(seat_counter),
                "status": "available",
                "reserved_by_reservation_id": None,
                "booked_by_booking_id": None,
                "side": "left",
                "row": row,
                "col": col,
                "created_at": datetime.utcnow()
            })
            seat_counter += 1
        for col in (1, 2):
            seats_docs.append({
                "bus_id": bus_obj_id,
                "seat_number": str(seat_counter),
                "status": "available",
                "reserved_by_reservation_id": None,
                "booked_by_booking_id": None,
                "side": "right",
                "row": row,
                "col": col,
                "created_at": datetime.utcnow()
            })
            seat_counter += 1
    return seats_docs


@router.post("/routes", status_code=201)
async def create_route(payload: RouteCreate):
    doc = payload.dict()
    doc["created_at"] = datetime.utcnow()
    res = await routes_col.insert_one(doc)
    return {"id": str(res.inserted_id)}


@router.post("/buses", status_code=201)
async def create_bus(payload: BusCreate):
    if not ObjectId.is_valid(payload.route_id):
        raise HTTPException(status_code=400, detail="Invalid route id")

    route = await routes_col.find_one({"_id": ObjectId(payload.route_id)})
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    doc = payload.dict()
    doc["route_id"] = ObjectId(payload.route_id)
    doc["created_at"] = datetime.utcnow()

    res = await buses_col.insert_one(doc)
    bus_obj_id = res.inserted_id

    seats_docs = _generate_40_seats(bus_obj_id)
    try:
        insert_res = await seats_col.insert_many(seats_docs)
        inserted = len(insert_res.inserted_ids)
    except Exception as e:
        try:
            await buses_col.delete_one({"_id": bus_obj_id})
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to initialize seats: {e}")

    return {"id": str(bus_obj_id), "seats_created": inserted}


@router.patch("/buses/{bus_id}")
async def update_bus(bus_id: str, fields: dict = Body(...)):
    if not ObjectId.is_valid(bus_id):
        raise HTTPException(status_code=400, detail="Invalid bus id")
    immutable = {"_id", "created_at", "route_id"}
    for k in immutable:
        if k in fields:
            del fields[k]
    await buses_col.update_one({"_id": ObjectId(bus_id)}, {"$set": fields})
    return {"status": "ok"}


@router.delete("/buses/{bus_id}")
async def delete_bus(bus_id: str):
    """
    Delete bus and related records (seats, bookings, transactions).
    Matches both ObjectId and string-stored bus_id fields.
    """
    if not ObjectId.is_valid(bus_id):
        raise HTTPException(status_code=400, detail="Invalid bus id")

    oid = ObjectId(bus_id)
    # delete bus document
    bus_del = await buses_col.delete_one({"_id": oid})

    # delete seats - match both ObjectId and string forms for bus_id
    seats_del = await seats_col.delete_many({"$or": [{"bus_id": oid}, {"bus_id": str(oid)}]})

    # delete bookings - match both forms
    bookings_del = await bookings_col.delete_many({"$or": [{"bus_id": oid}, {"bus_id": str(oid)}]})

    # delete transactions - match both forms
    transactions_del = await transactions_col.delete_many({"$or": [{"bus_id": oid}, {"bus_id": str(oid)}]})

    return {
        "status": "deleted",
        "bus_deleted": bus_del.deleted_count,
        "seats_deleted": seats_del.deleted_count,
        "bookings_deleted": bookings_del.deleted_count,
        "transactions_deleted": transactions_del.deleted_count
    }


def _parse_date_inclusive(start_str: str, end_str: str):
    """
    Robust parsing for date/time inputs from frontend.
    If input is YYYY-MM-DD (length 10) treat it as whole-day inclusive.
    Returns (start_dt, end_dt) both as datetimes.
    """
    try:
        start = datetime.fromisoformat(start_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid from_date format; use YYYY-MM-DD or ISO datetime")

    try:
        end = datetime.fromisoformat(end_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid to_date format; use YYYY-MM-DD or ISO datetime")

    # If the caller passed a date-only string like '2025-09-21' (len == 10),
    # datetime.fromisoformat produces midnight; make end inclusive by adding the remainder of the day.
    if len(end_str) == 10:
        end = datetime.combine(end.date(), time.max)  # 23:59:59.999999

    # If start is date-only, set start to start of day for clarity
    if len(start_str) == 10:
        start = datetime.combine(start.date(), time.min)

    return start, end


@router.get("/reports")
async def reports(
    from_date: str = Query(..., description="ISO date string, e.g. 2025-09-01"),
    to_date: str = Query(...),
    by: str = Query("day", regex="^(day|week|month|year)$"),
    bus_id: Optional[str] = None
):
    """
    Returns aggregated bookings grouped by day|week|month|year.
    - Supports date-only inputs (YYYY-MM-DD) and ISO datetimes.
    - If bus_id provided, will match either ObjectId or string-stored bus_id.
    """
    start, end = _parse_date_inclusive(from_date, to_date)

    # Build base match
    match = {"created_at": {"$gte": start, "$lte": end}}

    # bus_id matching: support both ObjectId and string stored bus ids
    if bus_id:
        if ObjectId.is_valid(bus_id):
            oid = ObjectId(bus_id)
            match["$or"] = [{"bus_id": oid}, {"bus_id": str(oid)}]
        else:
            match["bus_id"] = bus_id

    # Build aggregation pipeline based on 'by'
    if by == "day":
        fmt = "%Y-%m-%d"
        key_name = "day"
        group_id = {key_name: {"$dateToString": {"format": fmt, "date": "$created_at"}}}
        sort_key = f"_id.{key_name}"
    elif by == "month":
        fmt = "%Y-%m"
        key_name = "month"
        group_id = {key_name: {"$dateToString": {"format": fmt, "date": "$created_at"}}}
        sort_key = f"_id.{key_name}"
    elif by == "year":
        fmt = "%Y"
        key_name = "year"
        group_id = {key_name: {"$dateToString": {"format": fmt, "date": "$created_at"}}}
        sort_key = f"_id.{key_name}"
    else:
        # week grouping: produce a readable "YYYY-WW" label using iso week/year operators.
        # Note: this uses aggregation expressions ($isoWeekYear, $isoWeek) available in modern Mongo versions.
        key_name = "week"
        group_id = {
            key_name: {
                "$concat": [
                    {"$toString": {"$isoWeekYear": "$created_at"}},
                    "-W",
                    {
                        # zero-pad week number to 2 digits
                        "$cond": [
                            {"$lt": [{"$isoWeek": "$created_at"}, 10]},
                            {"$concat": ["0", {"$toString": {"$isoWeek": "$created_at"}}]},
                            {"$toString": {"$isoWeek": "$created_at"}}
                        ]
                    }
                ]
            }
        }
        sort_key = f"_id.{key_name}"

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": group_id,
            "revenue": {"$sum": {"$ifNull": ["$total_price", 0]}},
            "bookings": {"$sum": 1}
        }},
        {"$sort": {sort_key: 1}}
    ]

    agg = bookings_col.aggregate(pipeline)
    out = []
    async for doc in agg:
        out.append(doc)
    return {"data": out}


@router.get("/top-buses")
async def top_buses(
    period_from: str = Query(...),
    period_to: str = Query(...),
    limit: int = Query(10, ge=1, le=100)
):
    try:
        start = datetime.fromisoformat(period_from)
        end = datetime.fromisoformat(period_to)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format; use ISO8601")

    pipeline = [
        {"$match": {"created_at": {"$gte": start, "$lte": end}}},
        {"$group": {
            "_id": "$bus_id",
            "total_amount": {"$sum": {"$ifNull": ["$total_price", 0]}},
            "seats_booked": {"$sum": 1}
        }},
        {"$project": {
            "total_amount": 1,
            "seats_booked": 1,
            "booking_rate": {"$cond": [{"$eq": ["$seats_booked", 0]}, 0, {"$divide": ["$total_amount", "$seats_booked"]}]}
        }},
        {"$sort": {"booking_rate": -1}},
        {"$limit": limit}
    ]

    agg = bookings_col.aggregate(pipeline)
    out = []
    async for doc in agg:
        out.append({
            "bus_id": str(doc["_id"]) if doc.get("_id") is not None else None,
            "total_amount": doc.get("total_amount", 0),
            "seats_booked": doc.get("seats_booked", 0),
            "booking_rate": doc.get("booking_rate", 0)
        })
    return {"data": out}


@router.get("/routes")
async def list_routes(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=500)):
    cursor = routes_col.find({}).skip(skip).limit(limit)
    out = []
    async for r in cursor:
        r["_id"] = str(r["_id"])
        out.append(r)
    return {"routes": out, "skip": skip, "limit": limit}


@router.get("/buses")
async def list_buses(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=500)):
    cursor = buses_col.find({}).skip(skip).limit(limit)
    out = []
    async for b in cursor:
        b["_id"] = str(b["_id"])
        if isinstance(b.get("route_id"), ObjectId):
            b["route_id"] = str(b["route_id"])
        out.append(b)
    return {"buses": out, "skip": skip, "limit": limit}


@router.post("/buses/{bus_id}/open-sales")
async def open_sales(bus_id: str, weeks_before: int = Query(1, ge=0)):
    if not ObjectId.is_valid(bus_id):
        raise HTTPException(status_code=400, detail="Invalid bus id")
    bus = await buses_col.find_one({"_id": ObjectId(bus_id)})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    if "start_time" not in bus or not bus["start_time"]:
        raise HTTPException(status_code=400, detail="Bus start_time not set")
    st = bus["start_time"]
    if isinstance(st, str):
        try:
            st = datetime.fromisoformat(st)
        except Exception:
            raise HTTPException(status_code=400, detail="Bus start_time stored in invalid format")
    new_open = st - timedelta(weeks=weeks_before)
    await buses_col.update_one({"_id": bus["_id"]}, {"$set": {"sales_open_time": new_open}})
    return {"status": "ok", "sales_open_time": new_open.isoformat()}


@router.delete("/routes/{route_id}")
async def delete_route(route_id: str):
    if not ObjectId.is_valid(route_id):
        raise HTTPException(status_code=400, detail="Invalid route id")
    await routes_col.delete_one({"_id": ObjectId(route_id)})
    return {"status": "deleted"}
