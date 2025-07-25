from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from uuid import UUID, uuid4
from fastapi.security import OAuth2PasswordRequestForm

from ..schemas import UserOut, UserInDB, UserUpdate
from ..utils.auth import hash_password, get_current_user, verify_password, get_user_by_NationalID
from ..db import db


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])

async def login(form_data: OAuth2PasswordRequestForm):
    user = await get_user_by_NationalID(form_data.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return user

@router.post("/", response_model=UserOut)
async def create_user(
    fullname: str,
    NationalID: str,
    position: str,
    company_id: UUID,
    password: str
):
    existing_user = await db.users.find_one({"NationalID": NationalID})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this National ID already exists")

    user_data = {
        "id": str(uuid4()),
        "fullname": fullname,
        "NationalID": NationalID,
        "position": position,
        "company_id": company_id,
        "password": hash_password(password)
    }

    await db.users.insert_one(user_data)
    return UserOut(**user_data)

@router.get("/", response_model=list[UserOut])
async def list_users():
    docs = db.users.find({}, {"_id":0, "password":0})
    return [UserOut(**doc) async for doc in docs]

@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: UUID):
    doc = await db.users.find_one({"id": user_id}, {"_id":0, "password":0})
    if not doc:
        raise HTTPException(404, "User not found")
    return UserOut(**doc)

@router.get("/name/{name}", response_model=UserOut)
async def read_user_by_name(name: UUID):
    doc = await db.users.find_one({"fullname": name}, {"_id":0, "password":0})
    if not doc:
        raise HTTPException(404, "User not found")
    return UserOut(**doc)

@router.get("/company/{company_id}", response_model=list[UserOut])
async def list_users_by_company(company_id: UUID):
    cursor = db.users.find({"company_id": str(company_id)}, {"_id": 0, "password": 0})
    return [UserOut(**doc) async for doc in cursor]

@router.get("/search/", response_model=List[UserOut])
async def search_users_by_name(part: str = Query(..., min_length=1)):
    cursor = db.users.find(
        {"fullname": {"$regex": part, "$options": "i"}},  # нечувствительно к регистру
        {"_id": 0, "password": 0}
    )
    results = await cursor.to_list(length=50)  # ограничим количество результатов
    return [UserOut(**user) for user in results]

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: UUID, payload: UserUpdate):
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    res = await db.users.update_one({"id": user_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "User not found")
    return await read_user(user_id)

@router.delete("/{user_id}")
async def delete_user(user_id: UUID):
    res = await db.users.delete_one({"id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "User not found")
    return {"detail": "Deleted"}