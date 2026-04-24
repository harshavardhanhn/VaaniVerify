from datetime import UTC, datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


async def log_call_event(
    db: AsyncIOMotorDatabase,
    order_id: str,
    event: str,
    detail: Optional[str] = None,
    call_sid: Optional[str] = None,
) -> None:
    await db.call_logs.insert_one(
        {
            "order_id": order_id,
            "call_sid": call_sid,
            "event": event,
            "detail": detail,
            "created_at": datetime.now(UTC),
        }
    )
