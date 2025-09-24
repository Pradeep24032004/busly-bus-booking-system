
# routers/buses_routes.py
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from bson import ObjectId
from db import buses_col, routes_col, seats_col
from models import BusCreate, BusPublic
from routers.deps import get_current_user, require_admin

router = APIRouter(prefix="/buses", tags=["buses"])


def _generate_40_seats(bus_obj_id):
    """
    Generate a realistic 10-row bus layout with 4 seats per row (left: 2, right: 2).
    Seat numbering is row-wise: left1,left2,right1,right2 per row.
    """
    seats_docs = []
    seat_counter = 1
    ROWS = 10
    for row in range(1, ROWS + 1):
        # left two seats
        for col in (1, 2):
            seats_docs.append({
                "bus_id": bus_obj_id,
                "seat_number": str(seat_counter),
                "status": "available",
                "reserved_by_reservation_id": None,
                "booked_by_booking_id": None,
                "side": "left",
                "row": row,
                "col": col
            })
            seat_counter += 1

        # right two seats
        for col in (1, 2):
            seats_docs.append({
                "bus_id": bus_obj_id,
                "seat_number": str(seat_counter),
                "status": "available",
                "reserved_by_reservation_id": None,
                "booked_by_booking_id": None,
                "side": "right",
                "row": row,
                "col": col
            })
            seat_counter += 1

    return seats_docs


@router.post("/", response_model=dict, status_code=201, dependencies=[Depends(require_admin)])
async def create_bus(payload: BusCreate):
    """
    Create a bus and initialize seat documents.
    Admin-created buses always get 40 seats.
    """
    # Validate route id
    if not ObjectId.is_valid(payload.route_id):
        raise HTTPException(status_code=400, detail="Invalid route id")

    route = await routes_col.find_one({"_id": ObjectId(payload.route_id)})
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Prepare bus document
    doc = payload.dict()
    doc["route_id"] = ObjectId(payload.route_id)
    doc["created_at"] = datetime.utcnow()

    # Insert bus and keep ObjectId
    res = await buses_col.insert_one(doc)
    bus_obj_id = res.inserted_id  # ObjectId
    print(f"[DEBUG] Created bus with ID: {bus_obj_id}")

    # Initialize 40 seats using the same ObjectId
    seats_docs = _generate_40_seats(bus_obj_id)

    if seats_docs:
        try:
            print(f"[DEBUG] Inserting {len(seats_docs)} seats for bus {bus_obj_id}")
            seat_result = await seats_col.insert_many(seats_docs)
            inserted = len(seat_result.inserted_ids)
            print(f"[DEBUG] Successfully inserted {inserted} seats")
        except Exception as e:
            print(f"[ERROR] Failed to insert seats for bus {bus_obj_id}: {e}", flush=True)
            # If insertion failed, delete the created bus to avoid orphan bus (optional)
            try:
                await buses_col.delete_one({"_id": bus_obj_id})
                print(f"[DEBUG] Deleted bus {bus_obj_id} due to seat init failure")
            except Exception:
                pass
            raise HTTPException(status_code=500, detail="Failed to initialize seats")

        # Verify seats were actually inserted
        seat_count = await seats_col.count_documents({"bus_id": bus_obj_id})
        print(f"[DEBUG] Seat count verification: {seat_count} seats found for bus {bus_obj_id}")
    else:
        print(f"[DEBUG] No seats to insert for bus {bus_obj_id}")

    return {"id": str(bus_obj_id)}


@router.get("/search")
async def search(src: str = Query(...), dst: str = Query(...), date: Optional[str] = None):
    route = await routes_col.find_one({"src_city": src, "dst_city": dst})
    if not route:
        return {"buses": []}

    now = datetime.utcnow()
    cursor = buses_col.find({
        "route_id": route["_id"],
        "status": "published",
        "$or": [
            {"sales_open_time": {"$lte": now}},
            {"sales_open_time": None}
        ]
    })

    buses = []
    async for b in cursor:
        b["_id"] = str(b["_id"])
        b["route_id"] = str(b["route_id"])
        buses.append(b)
    return {"buses": buses}


@router.get("/{bus_id}")
async def get_bus(bus_id: str):
    print(f"[DEBUG] Getting bus details for ID: {bus_id}")

    if not ObjectId.is_valid(bus_id):
        raise HTTPException(status_code=400, detail="Invalid bus id")

    bus = await buses_col.find_one({"_id": ObjectId(bus_id)})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    print(f"[DEBUG] Found bus: {bus.get('name', 'Unknown')} with ID: {bus['_id']}")

    seats = []
    bus_object_id = ObjectId(bus_id)

    print(f"[DEBUG] Looking for seats with bus_id: {bus_object_id} (type: {type(bus_object_id)})")

    # Primary attempt: seats linked with ObjectId bus_id
    seats_cursor = seats_col.find({"bus_id": bus_object_id})
    async for s in seats_cursor:
        seats.append({
            "_id": str(s.get("_id")),
            "seat_number": str(s.get("seat_number")),
            "status": s.get("status", "available"),
            "side": s.get("side"),
            "row": s.get("row"),
            "col": s.get("col")
        })

    print(f"[DEBUG] Found {len(seats)} seats with ObjectId lookup")

    # Fallback: string lookup
    if not seats:
        print(f"[DEBUG] No seats found with ObjectId, trying string lookup...")
        seats_cursor2 = seats_col.find({"bus_id": str(bus["_id"])})
        async for s in seats_cursor2:
            seats.append({
                "_id": str(s.get("_id")),
                "seat_number": str(s.get("seat_number")),
                "status": s.get("status", "available"),
                "side": s.get("side"),
                "row": s.get("row"),
                "col": s.get("col")
            })
        print(f"[DEBUG] Found {len(seats)} seats with string lookup")

    # Debug: show sample if still empty
    if not seats:
        total_seats = await seats_col.count_documents({})
        print(f"[DEBUG] No seats found for this bus. Total seats in collection: {total_seats}")

        sample_seats = []
        async for s in seats_col.find({}).limit(3):
            sample_seats.append({
                "bus_id": str(s.get("bus_id")),
                "bus_id_type": type(s.get("bus_id")).__name__,
                "seat_number": s.get("seat_number"),
                "side": s.get("side"),
                "row": s.get("row"),
                "col": s.get("col")
            })
        print(f"[DEBUG] Sample seats in collection: {sample_seats}")

    # Sort seats numerically where possible
    try:
        seats.sort(key=lambda x: int(x["seat_number"]))
    except Exception:
        seats.sort(key=lambda x: x["seat_number"])

    bus["_id"] = str(bus["_id"])
    bus["route_id"] = str(bus["route_id"])

    print(f"[DEBUG] Returning {len(seats)} seats for bus {bus_id}")
    return {"bus": bus, "seats": seats}


@router.post("/{bus_id}/create-seats", dependencies=[Depends(require_admin)])
async def create_seats_for_bus(bus_id: str, seats_count: int = 40):
    """
    Create or recreate seats for an existing bus. Deletes old seats linked to this bus id first.
    """
    print(f"[DEBUG] Creating seats for bus {bus_id}")

    if not ObjectId.is_valid(bus_id):
        raise HTTPException(status_code=400, detail="Invalid bus id")

    bus = await buses_col.find_one({"_id": ObjectId(bus_id)})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    bus_obj_id = ObjectId(bus_id)

    # Delete existing seats first (if any)
    delete_result = await seats_col.delete_many({"bus_id": bus_obj_id})
    print(f"[DEBUG] Deleted {delete_result.deleted_count} existing seats")

    # Always create the 40-seat realistic layout
    seats_docs = _generate_40_seats(bus_obj_id)

    if seats_docs:
        try:
            result = await seats_col.insert_many(seats_docs)
            print(f"[DEBUG] Created {len(result.inserted_ids)} seats")
            return {"message": f"Created {len(result.inserted_ids)} seats for bus {bus_id}"}
        except Exception as e:
            print(f"[ERROR] insert_many failed: {e}", flush=True)
            raise HTTPException(status_code=500, detail="Failed to create seats")
    return {"message": "No seats created"}


@router.get("/{bus_id}/debug")
async def debug_bus_seats(bus_id: str):
    if not ObjectId.is_valid(bus_id):
        raise HTTPException(status_code=400, detail="Invalid bus id")

    bus_obj_id = ObjectId(bus_id)
    bus = await buses_col.find_one({"_id": bus_obj_id})

    seats_with_objectid = []
    async for s in seats_col.find({"bus_id": bus_obj_id}):
        seats_with_objectid.append(s)

    seats_with_string = []
    async for s in seats_col.find({"bus_id": str(bus_obj_id)}):
        seats_with_string.append(s)

    total_seats = await seats_col.count_documents({})

    def _normalize_sample(s):
        return {
            "_id": str(s.get("_id")),
            "seat_number": str(s.get("seat_number")),
            "side": s.get("side"),
            "row": s.get("row"),
            "col": s.get("col"),
            "status": s.get("status")
        }

    return {
        "bus_exists": bus is not None,
        "bus_id_searched": str(bus_obj_id),
        "seats_with_objectid_count": len(seats_with_objectid),
        "seats_with_string_count": len(seats_with_string),
        "total_seats_in_collection": total_seats,
        "seats_sample_objectid": [_normalize_sample(s) for s in seats_with_objectid[:2]] if seats_with_objectid else [],
        "seats_sample_string": [_normalize_sample(s) for s in seats_with_string[:2]] if seats_with_string else []
    }
