from datetime import datetime
from fastapi import APIRouter, Form, HTTPException, Depends, UploadFile, File
from uuid import UUID, uuid4
import shutil
import os

from ..schemas import PostOut, PostCreate, PostInDB, PostUpdate, UserInDB
from ..utils.auth import get_current_user
from ..db import db


router = APIRouter(prefix="/company/posts", tags=["posts"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=PostOut)
async def create_post(
    content: str = Form(...),
    image: UploadFile = File(None),
    user: UserInDB = Depends(get_current_user)
):
    post_id = uuid4()
    image_path = None

    if image:
        save_dir = "static/post_images"
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{uuid4().hex}_{image.filename}"
        full_path = os.path.join(save_dir, filename)

        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        image_path = f"/{save_dir}/{filename}"

    post_data = {
        "id": post_id,
        "content": content,
        "image": image_path,
        "sender_id": user.id,
        "company_id": user.company_id,
        "timestamp": datetime.utcnow(),
        "likes": 0
    }

    await db.post.insert_one(post_data)
    return PostOut(**post_data)

@router.get("/", response_model=list[PostOut])
async def list_posts():
    docs = db.post.find({}, {"_id":0})
    return [PostOut(**doc) async for doc in docs]

@router.get("/{company_id}", response_model=list[PostOut])
async def list_posts(company_id: UUID):
    docs = db.post.find({"company_id": company_id}, {"_id":0})
    return [PostOut(**doc) async for doc in docs]


@router.get("/{post_id}", response_model=PostOut)
async def read_post(post_id: UUID):
    doc = await db.post.find_one({"id": post_id}, {"_id":0})
    if not doc:
        raise HTTPException(404, "Post not found")
    return PostOut(**doc)

@router.put("/{post_id}", response_model=PostOut)
async def update_post(post_id: UUID, payload: PostUpdate):
    data = payload.model_dump(exclude_unset=True)
    res = await db.post.update_one({"id": post_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Post not found")
    return await read_post(post_id)

@router.delete("/{post_id}")
async def delete_post(post_id: UUID):
    res = await db.post.delete_one({"id": post_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Post not found")
    return {"detail": "Deleted"}

@router.post("/{post_id}/like", response_model=PostOut)
async def like_post(post_id: UUID):
    res = await db.post.update_one({"id": post_id}, {"$inc": {"likes": 1}})
    if res.matched_count == 0:
        raise HTTPException(404, "Post not found")
    return await read_post(post_id)