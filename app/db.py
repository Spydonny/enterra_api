from motor.motor_asyncio import AsyncIOMotorClient

from app.settings import settings
from .schemas import UserInDB

client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")
db = client["enterra_db-dev"]
