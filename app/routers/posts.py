from datetime import datetime
from fastapi import APIRouter, Form, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional
from uuid import UUID, uuid4
import shutil
import os

from ..schemas import PostOut, PostCreate, PostInDB, PostUpdate, UserInDB
from ..utils.auth import get_current_user
from ..utils.helpers import get_company_name, save_img
from ..db import db


router = APIRouter(prefix="/company/posts", tags=["posts"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=PostOut)
async def create_post(
    content: str = Form(...),
    image: UploadFile = File(None),
    user: UserInDB = Depends(get_current_user)
):
    post_id = uuid4()
    image_path = save_img("post_image", image) if image else None
    company_name = await get_company_name(user.company_id)

    post_data = {
        "id": post_id,
        "content": content,
        "image": image_path,
        "sender_id": user.id,
        "sender_name": user.fullname,
        "company_id": user.company_id,
        "company_name": company_name,
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

@router.get("/search/", response_model=List[PostOut])
async def search_posts(part: str = Query(..., min_length=1)):
    cursor = db.posts.find(
        {
            "$or": [
                {"company_name": {"$regex": part, "$options": "i"}},
                {"content": {"$regex": part, "$options": "i"}},
                {"sender_name": {"$regex": part, "$options": "i"}}
            ]
        },
        {"_id": 0}
    )
    results = await cursor.to_list(length=50)
    return [PostOut(**doc) for doc in results]