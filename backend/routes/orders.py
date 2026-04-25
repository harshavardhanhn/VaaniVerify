from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.config import get_settings
from backend.database import get_db
from backend.models.order import OrderCreateRequest, OrderOut, OrderStatus, order_document_to_out
from backend.routes.shared import log_call_event
from backend.services.language import normalize_language
from backend.services.twilio_service import twilio_service
from backend.utils.auth import verify_session_token


router = APIRouter(tags=["orders"])
settings = get_settings()


def _require_session(request: Request) -> dict:
    token = request.cookies.get("vv_session")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        return verify_session_token(token, settings.auth_session_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


def require_user_or_admin(request: Request) -> dict:
    session = _require_session(request)
    if session.get("role") not in {"user", "admin", "customer"}:
        raise HTTPException(status_code=403, detail="User access required.")
    return session


def require_admin(request: Request) -> dict:
    session = _require_session(request)
    if session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return session


@router.post("/create-order", response_model=OrderOut)
async def create_order(payload: OrderCreateRequest, _: dict = Depends(require_user_or_admin)) -> OrderOut:
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
        "total_amount": payload.total_amount,
        "categories": payload.categories,
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
async def list_orders(_: dict = Depends(require_admin)) -> list[OrderOut]:
    db = get_db()
    cursor = db.orders.find().sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [order_document_to_out(doc) for doc in docs]


@router.get("/api/analytics")
async def get_analytics(_: dict = Depends(require_admin)) -> dict:
    db = get_db()
    
    # 1. Orders by Status
    status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    status_counts = {doc["_id"]: doc["count"] async for doc in db.orders.aggregate(status_pipeline)}
    
    # 2. Orders by Language
    lang_pipeline = [{"$group": {"_id": "$language_preference", "count": {"$sum": 1}}}]
    lang_counts = {doc["_id"]: doc["count"] async for doc in db.orders.aggregate(lang_pipeline)}
    
    # 3. Total Sales Revenue (only confirmed orders)
    sales_pipeline = [
        {"$match": {"status": "Confirmed"}},
        {"$group": {"_id": None, "total_revenue": {"$sum": {"$ifNull": ["$total_amount", 4500.0]}}}}
    ]
    sales_result = [doc async for doc in db.orders.aggregate(sales_pipeline)]
    total_revenue = sales_result[0]["total_revenue"] if sales_result else 0.0

    # 4. Orders by Category (unwind array, count)
    cat_pipeline = [
        {"$match": {"status": "Confirmed"}},
        {"$project": {"categories": {"$ifNull": ["$categories", ["electronics", "kitchen"]]}}},
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "count": {"$sum": 1}}}
    ]
    category_counts = {doc["_id"]: doc["count"] async for doc in db.orders.aggregate(cat_pipeline)}

    return {
        "status_counts": status_counts,
        "language_counts": lang_counts,
        "category_counts": category_counts,
        "total_revenue": total_revenue,
        "total_orders": sum(status_counts.values())
    }
