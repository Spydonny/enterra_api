from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID, uuid4
from datetime import datetime
from ..models import ReviewCreate, ReviewInDB, ReviewUpdate
from ..schemas import ReviewOut
from ..auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=ReviewOut)
async def create_review(payload: ReviewCreate):
    data = payload.dict()
    data.update({"id": uuid4(), "reviewer_id": get_current_user().id,
                 "timestamp": datetime.utcnow()})
    await router.state.db.review.insert_one(data)
    return ReviewOut(**data)

@router.get("/", response_model=list[ReviewOut])
async def list_reviews():
    docs = router.state.db.review.find({}, {"_id":0}).sort("timestamp", -1)
    return [ReviewOut(**doc) async for doc in docs]

@router.get("/{review_id}", response_model=ReviewOut)
async def read_review(review_id: UUID):
    doc = await router.state.db.review.find_one({"id": review_id}, {"_id":0})
    if not doc:
        raise HTTPException(404, "Review not found")
    return ReviewOut(**doc)

@router.put("/{review_id}", response_model=ReviewOut)
async def update_review(review_id: UUID, payload: ReviewUpdate):
    data = payload.dict(exclude_unset=True)
    res = await router.state.db.review.update_one({"id": review_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Review not found")
    return await read_review(review_id)

@router.delete("/{review_id}")
async def delete_review(review_id: UUID):
    res = await router.state.db.review.delete_one({"id": review_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Review not found")
    return {"detail": "Deleted"}