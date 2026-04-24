from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from backend.database import get_db
from backend.models.order import OrderCreateRequest, OrderOut, OrderStatus, order_document_to_out
from backend.routes.shared import log_call_event
from backend.services.language import normalize_language
from backend.services.twilio_service import twilio_service


router = APIRouter(tags=["orders"])


@router.post("/create-order", response_model=OrderOut)
async def create_order(payload: OrderCreateRequest) -> OrderOut:
    db = get_db()
    now = datetime.now(UTC)
    language = normalize_language(payload.language_preference)

    order_doc = {
        "customer_name": payload.customer_name,
        "phone_number": payload.phone_number,
        "order_details": payload.order_details,
        "language_preference": language,
        "status": OrderStatus.pending.value,
        "retry_count": 0,
        "last_intent": None,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.orders.insert_one(order_doc)
    order_doc["_id"] = result.inserted_id

    if payload.auto_trigger_call:
        call_sid = twilio_service.initiate_call(payload.phone_number, str(result.inserted_id), attempt=1)
        await log_call_event(
            db=db,
            order_id=str(result.inserted_id),
            event="CALL_INITIATED",
            detail=f"Call started via create-order. SID: {call_sid}",
            call_sid=call_sid,
        )

    return order_document_to_out(order_doc)


@router.get("/orders", response_model=list[OrderOut])
async def list_orders() -> list[OrderOut]:
    db = get_db()
    cursor = db.orders.find().sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [order_document_to_out(doc) for doc in docs]
