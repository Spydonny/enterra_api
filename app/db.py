from motor.motor_asyncio import AsyncIOMotorClient

from app.settings import settings
from .models import UserInDB

client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")
db = client["enterra"]

async def get_user_by_email(email: str) -> UserInDB | None:
    data = await db.users.find_one({"email": email})
    if data:
        return UserInDB(**data)
    return None
