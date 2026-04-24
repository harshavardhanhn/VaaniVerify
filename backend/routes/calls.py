from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models.order import TriggerCallRequest
from backend.routes.shared import log_call_event
from backend.services.twilio_service import twilio_service
from backend.utils.object_id import parse_object_id


router = APIRouter(tags=["calls"])


@router.post("/trigger-call")
async def trigger_call(payload: TriggerCallRequest) -> dict:
    db = get_db()
    oid = parse_object_id(payload.order_id)

    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    call_sid = twilio_service.initiate_call(order["phone_number"], payload.order_id, attempt=1)

    await log_call_event(
        db=db,
        order_id=payload.order_id,
        event="CALL_INITIATED",
        detail=f"Call triggered manually. SID: {call_sid}",
        call_sid=call_sid,
    )

    return {"success": True, "call_sid": call_sid, "order_id": payload.order_id}


@router.get("/logs")
async def get_logs(limit: int = 50) -> list[dict]:
    db = get_db()
    cursor = db.call_logs.find().sort("created_at", -1).limit(min(limit, 200))
    logs = await cursor.to_list(length=min(limit, 200))
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs
