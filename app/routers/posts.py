from datetime import datetime
from fastapi import APIRouter, Form, HTTPException, Depends, UploadFile, File
from uuid import UUID, uuid4
from ..models import PostCreate, PostInDB, PostUpdate
from ..schemas import PostOut
from ..auth import get_current_user


router = APIRouter(prefix="/posts", tags=["posts"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=PostOut)
async def create_post(content: str = Form(...), image: UploadFile = File(None)):
    data = {"content": content, "image": image.filename if image else None, "sender_id": get_current_user().id}
    data["id"] = uuid4()
    data["timestamp"] = datetime.now()
    data["likes"] = 0
    await router.state.db.post.insert_one(data)
    return PostOut(**data)

@router.get("/", response_model=list[PostOut])
async def list_posts():
    docs = router.state.db.post.find({}, {"_id":0})
    return [PostOut(**doc) async for doc in docs]

@router.get("/{post_id}", response_model=PostOut)
async def read_post(post_id: UUID):
    doc = await router.state.db.post.find_one({"id": post_id}, {"_id":0})
    if not doc:
        raise HTTPException(404, "Post not found")
    return PostOut(**doc)

@router.put("/{post_id}", response_model=PostOut)
async def update_post(post_id: UUID, payload: PostUpdate):
    data = payload.dict(exclude_unset=True)
    res = await router.state.db.post.update_one({"id": post_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Post not found")
    return await read_post(post_id)

@router.delete("/{post_id}")
async def delete_post(post_id: UUID):
    res = await router.state.db.post.delete_one({"id": post_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Post not found")
    return {"detail": "Deleted"}

@router.post("/{post_id}/like", response_model=PostOut)
async def like_post(post_id: UUID):
    res = await router.state.db.post.update_one({"id": post_id}, {"$inc": {"likes": 1}})
    if res.matched_count == 0:
        raise HTTPException(404, "Post not found")
    return await read_post(post_id)