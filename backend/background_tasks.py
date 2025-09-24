from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import reservations_col, buses_col, transactions_col, seats_col
from datetime import datetime, timedelta
from config import settings
from seat_lock_manager import SeatLockManager
from bson import ObjectId

sched = AsyncIOScheduler()
lock_manager = SeatLockManager()

async def cleanup_expired_reservations():
    now = datetime.utcnow()
    cursor = reservations_col.find({"status": "pending", "expires_at": {"$lte": now}})
    async for res in cursor:
        # mark seats available if still reserved by this reservation
        await seats_col.update_many(
            {"bus_id": res["bus_id"], "seat_number": {"$in": res["seat_numbers"]},
             "reserved_by_reservation_id": res["_id"]},
            {"$set": {"status": "available", "reserved_by_reservation_id": None}}
        )
        await reservations_col.update_one({"_id": res["_id"]}, {"$set": {"status": "cancelled"}})
        lock_manager.release_many(str(res["bus_id"]), res["seat_numbers"], str(res["_id"]))

async def finalize_buses():
    now = datetime.utcnow()
    threshold = now + timedelta(minutes=20)
    cursor = buses_col.find({"status": "published", "start_time": {"$lte": threshold}})
    async for bus in cursor:
        # finalize bus: mark as finalized
        await buses_col.update_one({"_id": bus["_id"]}, {"$set": {"status": "finalized"}})
        # settle transactions for this bus
        await transactions_col.update_many(
            {"description": {"$regex": str(bus["_id"])}, "status": "held"},
            {"$set": {"status": "settled", "settled_at": datetime.utcnow()}}
        )
        # optionally unpublish or remove bus from search
        # await buses_col.update_one({"_id": bus["_id"]}, {"$set": {"status": "finalized", "published": False}})

def start_scheduler():
    sched.add_job(cleanup_expired_reservations, 'interval', seconds=30, id="cleanup_reservations")
    sched.add_job(finalize_buses, 'interval', seconds=60, id="finalize_buses")
    sched.start()
