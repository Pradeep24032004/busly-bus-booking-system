
# routers/admin_topups.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from routers.deps import require_admin
from db import users_col, topup_requests_col, transactions_col
from datetime import datetime
from bson import ObjectId
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/admin", tags=["admin"])  # don't use router-level require_admin so we can inject admin

def _to_objectid_if_possible(val):
    try:
        if ObjectId.is_valid(val):
            return ObjectId(val)
    except Exception:
        pass
    return None


@router.get("/topup-requests")
async def list_topup_requests(status: Optional[str] = Query(None), admin=Depends(require_admin)):
    """
    List top-up requests; admin must be authenticated. Optional filter by status.
    """
    q = {}
    if status:
        q["status"] = status
    cursor = topup_requests_col.find(q).sort("created_at", -1).limit(200)
    out = []
    async for r in cursor:
        user_id = r.get("user_id")
        user_info = None
        # try ObjectId lookup
        oid = _to_objectid_if_possible(user_id)
        if oid:
            u = await users_col.find_one({"_id": oid}, {"password_hash": 0})
            if u:
                user_info = {"id": str(u["_id"]), "email": u.get("email"), "name": u.get("name")}
        if not user_info:
            # try string id
            u = await users_col.find_one({"_id": str(user_id)}, {"password_hash": 0})
            if u:
                user_info = {"id": str(u["_id"]), "email": u.get("email"), "name": u.get("name")}
        out.append({
            "id": str(r.get("_id")),
            "user": user_info,
            "amount": float(r.get("amount", 0.0)),
            "note": r.get("note"),
            "status": r.get("status"),
            "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
            "approved_by": str(r.get("approved_by")) if r.get("approved_by") else None,
            "approved_at": r.get("approved_at").isoformat() if r.get("approved_at") else None,
            "rejected_reason": r.get("rejected_reason")
        })
    return {"requests": out}


@router.post("/topup-requests/{request_id}/approve")
async def approve_topup_request(request_id: str, admin=Depends(require_admin)):
    """
    Approve a top-up request: credit user balance, create transaction record.
    admin is the admin user document (returned by require_admin)
    """
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request id")
    rid = ObjectId(request_id)
    req = await topup_requests_col.find_one({"_id": rid})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request not pending")

    user_id = req.get("user_id")
    uid_oid = _to_objectid_if_possible(user_id)

    # read user
    user_q = {"_id": uid_oid} if uid_oid else {"_id": str(user_id)}
    user_doc = await users_col.find_one(user_q)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # update balance
    amount = float(req.get("amount", 0.0))
    current_balance = float(user_doc.get("balance", 0.0))
    new_balance = current_balance + amount

    await users_col.update_one(user_q, {"$set": {"balance": new_balance}})

    # create transaction record
    tx = {
        "from_user_id": None,
        "to_user_id": str(user_doc["_id"]),
        "amount": amount,
        "status": "settled",
        "description": f"Top-up approved by admin (request {request_id})",
        "timestamp": datetime.utcnow(),
        "approved_by_admin": str(admin.get("_id"))
    }
    await transactions_col.insert_one(tx)

    # update request status with real admin id
    await topup_requests_col.update_one({"_id": rid}, {"$set": {
        "status": "approved",
        "approved_by": str(admin.get("_id")),
        "approved_at": datetime.utcnow()
    }})

    return {"status": "approved", "amount": amount, "new_balance": new_balance}


@router.post("/topup-requests/{request_id}/reject")
async def reject_topup_request(request_id: str, payload: Dict[str, Any] = Body(...), admin=Depends(require_admin)):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request id")
    rid = ObjectId(request_id)
    reason = payload.get("reason", "Rejected by admin")
    req = await topup_requests_col.find_one({"_id": rid})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request not pending")
    await topup_requests_col.update_one({"_id": rid}, {"$set": {
        "status": "rejected",
        "rejected_reason": reason,
        "approved_at": datetime.utcnow(),
        "approved_by": str(admin.get("_id"))
    }})
    return {"status": "rejected", "reason": reason}

