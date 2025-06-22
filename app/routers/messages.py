from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from uuid import UUID, uuid4
from datetime import datetime
from ..models import MessageCreate, MessageInDB, MessageUpdate
from ..schemas import MessageOut
from ..auth import get_current_user
from ..db import db

router = APIRouter(prefix="/messages", tags=["messages"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=MessageOut)
async def create_message(payload: MessageCreate, image: UploadFile = File(None)):
    data = payload.dict()
    user = get_current_user()
    data.update({"id": uuid4(), "sender_id": user.id,
                 "image": image.filename if image else None,
                 "timestamp": datetime.utcnow(), "status": "loading"})
    await db.message.insert_one(data)
    return MessageOut(**data)

@router.get("/", response_model=list[MessageOut])
async def list_messages():
    docs = db.message.find({}, {"_id":0})
    return [MessageOut(**doc) async for doc in docs]

@router.get("/{message_id}", response_model=MessageOut)
async def read_message(message_id: UUID):
    doc = await db.message.find_one({"id": message_id}, {"_id":0})
    if not doc:
        raise HTTPException(404, "Message not found")
    return MessageOut(**doc)

@router.put("/{message_id}", response_model=MessageOut)
async def update_message(message_id: UUID, payload: MessageUpdate):
    data = payload.dict(exclude_unset=True)
    res = await db.message.update_one({"id": message_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Message not found")
    return await read_message(message_id)

@router.delete("/{message_id}")
async def delete_message(message_id: UUID):
    res = await db.message.delete_one({"id": message_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Message not found")
    return {"detail": "Deleted"}