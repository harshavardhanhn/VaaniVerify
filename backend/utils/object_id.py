from bson import ObjectId
from fastapi import HTTPException


def parse_object_id(order_id: str) -> ObjectId:
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order_id.")
    return ObjectId(order_id)
