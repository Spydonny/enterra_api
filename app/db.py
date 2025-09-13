from motor.motor_asyncio import AsyncIOMotorClient

from app.settings import settings
from .schemas import UserInDB

client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")
db = client["db_prod0ucti0on00"]
