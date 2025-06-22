from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID, uuid4
from fastapi.security import OAuth2PasswordRequestForm

from ..models import UserCreate, UserInDB, UserUpdate
from ..schemas import UserOut
from ..auth import hash_password, get_current_user, verify_password
from ..db import get_user_by_email


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])

async def login(form_data: OAuth2PasswordRequestForm):
    user = await get_user_by_email(form_data.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return user


@router.post("/", response_model=UserOut)
async def create_user(payload: UserCreate):
    data = payload.dict()
    data["id"] = uuid4()
    data["password"] = hash_password(data["password"])
    await router.state.db.user.insert_one(data)
    return UserOut(**data)

@router.get("/", response_model=list[UserOut])
async def list_users():
    docs = router.state.db.user.find({}, {"_id":0, "password":0})
    return [UserOut(**doc) async for doc in docs]

@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: UUID):
    doc = await router.state.db.user.find_one({"id": user_id}, {"_id":0, "password":0})
    if not doc:
        raise HTTPException(404, "User not found")
    return UserOut(**doc)

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: UUID, payload: UserUpdate):
    data = payload.dict(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    res = await router.state.db.user.update_one({"id": user_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "User not found")
    return await read_user(user_id)

@router.delete("/{user_id}")
async def delete_user(user_id: UUID):
    res = await router.state.db.user.delete_one({"id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "User not found")
    return {"detail": "Deleted"}