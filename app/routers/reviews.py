from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID, uuid4
from datetime import datetime
from ..schemas import ReviewOut, ReviewCreate, ReviewInDB, ReviewUpdate
from ..utils.auth import get_current_user
from ..db import db
from ..schemas import UserOut

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/", response_model=ReviewOut)
async def create_review(payload: ReviewCreate, current_user: UserOut = Depends(get_current_user)):
    data = payload.model_dump()
    data.update({"id": uuid4(), "reviewer_id": current_user.id, "reviewer_name": current_user.fullname,
                 "timestamp": datetime.utcnow()})
    await db.review.insert_one(data)
    return ReviewOut(**data)

@router.get("/", response_model=list[ReviewOut])
async def list_reviews():
    docs = db.review.find({}, {"_id":0}).sort("timestamp", -1)
    return [ReviewOut(**doc) async for doc in docs]

@router.get("/{review_id}", response_model=ReviewOut)
async def read_review(review_id: UUID):
    doc = await db.review.find_one({"id": review_id}, {"_id":0})
    if not doc:
        raise HTTPException(404, "Review not found")
    return ReviewOut(**doc)

@router.get("/user/{user_id}", response_model=list[ReviewOut])
async def list_user_reviews(user_id: UUID):
    docs = db.review.find({"reviewer_id": user_id}, {"_id":0}).sort("timestamp", -1)
    return [ReviewOut(**doc) async for doc in docs]

@router.get("/company/{company_id}", response_model=list[ReviewOut])
async def list_product_reviews(company_id: UUID):
    docs = db.review.find({"company_id": company_id}, {"_id":0}).sort("timestamp", -1)
    return [ReviewOut(**doc) async for doc in docs]


@router.put("/{review_id}", response_model=ReviewOut)
async def update_review(review_id: UUID, payload: ReviewUpdate):
    data = payload.model_dump(exclude_unset=True)
    res = await db.review.update_one({"id": review_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Review not found")
    return await read_review(review_id)

@router.delete("/{review_id}")
async def delete_review(review_id: UUID):
    res = await db.review.delete_one({"id": review_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Review not found")
    return {"detail": "Deleted"}