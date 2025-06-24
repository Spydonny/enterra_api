from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from uuid import UUID, uuid4
from datetime import datetime

from ..schemas import MessageOut, MessageCreate, UserInDB, MessageUpdate, MessageRoomCreate, MessageRoomOut
from ..utils.auth import get_current_user
from ..db import db
from ..utils.helpers import save_img

router = APIRouter(prefix="/messages", tags=["messages"], dependencies=[Depends(get_current_user)])

@router.post("/rooms/", response_model=MessageRoomOut)
async def create_message_room(
    payload: MessageRoomCreate,
    user: UserInDB = Depends(get_current_user)
):
    data = payload.model_dump()
    data["created_at"] = datetime.utcnow()

    # Добавим текущего пользователя (автора) в список участников
    if user.id not in data["participants"]:
        data["participants"].append(user.id)

    # --- Групповой чат ---
    if data["is_group"]:
        data["id"] = uuid4()
        await db.message_rooms.insert_one(data)
        return MessageRoomOut(**data)

    # --- Персональный чат (должен быть уникальным по участникам) ---
    if len(data["participants"]) != 2:
        raise HTTPException(status_code=400, detail="Private chat must have exactly two participants.")

    # Сортируем участников для гарантии одинакового порядка
    sorted_participants = sorted(str(uid) for uid in data["participants"])
    
    # Ищем уже существующий персональный чат с теми же участниками
    existing = await db.message_rooms.find_one({
        "is_group": False,
        "participants": {"$all": sorted_participants, "$size": 2}
    })

    if existing:
        return MessageRoomOut(**existing)

    data["id"] = uuid4()
    data["participants"] = sorted_participants  # сохраняем в отсортированном виде
    await db.message_rooms.insert_one(data)
    return MessageRoomOut(**data)


@router.post("/{message_room_id}", response_model=MessageOut)
async def create_message(
    message_room_id: UUID,
    payload: MessageCreate,
    image: UploadFile = File(None),
    user: UserInDB = Depends(get_current_user)
):
    data = payload.model_dump()

    data.update({
        "id": uuid4(),
        "room_id": message_room_id,
        "sender_id": user.id,
        "image": image.filename if image else None,
        "timestamp": datetime.utcnow(),
        "status": "loading", 
        "image": save_img('message', image) if image else None
    })
    await db.message.insert_one(data)
    return MessageOut(**data)

@router.get("/{message_room_id}", response_model=list[MessageOut])
async def list_messages(message_room_id: UUID):
    docs = db.message.find({"message_room_id": message_room_id}, {"_id": 0})
    return [MessageOut(**doc) async for doc in docs]

@router.get("/{message_room_id}/{message_id}", response_model=MessageOut)
async def read_message(message_room_id: UUID, message_id: UUID):
    doc = await db.message.find_one({"id": message_id, "message_room_id": message_room_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Message not found")
    return MessageOut(**doc)

@router.put("/{message_room_id}/{message_id}", response_model=MessageOut)
async def update_message(message_room_id: UUID, message_id: UUID, payload: MessageUpdate):
    data = payload.dict(exclude_unset=True)
    res = await db.message.update_one(
        {"id": message_id, "message_room_id": message_room_id},
        {"$set": data}
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Message not found")
    return await read_message(message_room_id, message_id)

@router.delete("/{message_room_id}/{message_id}")
async def delete_message(message_room_id: UUID, message_id: UUID):
    res = await db.message.delete_one({"id": message_id, "message_room_id": message_room_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Message not found")
    return {"detail": "Deleted"}