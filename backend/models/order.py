from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    pending = "Pending"
    confirmed = "Confirmed"
    cancelled = "Cancelled"


class OrderCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    phone_number: str = Field(..., min_length=8)
    order_details: str = Field(..., min_length=3)
    language_preference: str = Field(default="en")
    auto_trigger_call: bool = Field(default=True)


class TriggerCallRequest(BaseModel):
    order_id: str


class OrderOut(BaseModel):
    id: str
    customer_name: str
    phone_number: str
    order_details: str
    language_preference: str
    status: OrderStatus
    retry_count: int = 0
    last_intent: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CallLog(BaseModel):
    order_id: str
    call_sid: Optional[str] = None
    event: str
    detail: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def order_document_to_out(doc: dict[str, Any]) -> OrderOut:
    return OrderOut(
        id=str(doc["_id"]),
        customer_name=doc["customer_name"],
        phone_number=doc["phone_number"],
        order_details=doc["order_details"],
        language_preference=doc["language_preference"],
        status=doc["status"],
        retry_count=doc.get("retry_count", 0),
        last_intent=doc.get("last_intent"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
