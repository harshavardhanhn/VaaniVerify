from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from backend.config import get_settings


_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


def connect_to_mongo() -> None:
    global _client, _database
    settings = get_settings()
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            maxPoolSize=20,
            minPoolSize=2,
            maxIdleTimeMS=300000,
            connectTimeoutMS=8000,
            serverSelectionTimeoutMS=8000,
        )
        _database = _client[settings.mongodb_db_name]


def close_mongo_connection() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None


def get_db() -> AsyncIOMotorDatabase:
    if _database is None:
        connect_to_mongo()
    if _database is None:
        raise RuntimeError("MongoDB database is not initialized.")
    return _database
