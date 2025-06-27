from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

from .users import login as user_login
from ..utils.auth import get_user_by_NationalID, get_companies, create_access_token, get_current_user, hash_password
from ..db import db
from ..models import TokenResponse
from ..schemas import UserOut
from ..utils.helpers import save_img


router = APIRouter( tags=["auth"])

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await user_login(form_data)  
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.NationalID}) 
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut)
async def register(
    company_id: UUID = Form(...),
    fullname: str = Form(...),
    NationalID: str = Form(..., min_length=12, max_length=12),
    position: str = Form(...),
    password: str = Form(...),
    avatar: Optional[UploadFile] = File(None)
):
    if await get_user_by_NationalID(NationalID):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NatinalID already registered"
        )
    
    doc = await db.company.find_one({"id": str(company_id)})

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    doc = await db.users.find_one({"company_id": str(company_id), "NationalID": NationalID})
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this NationalID already exists in this company"
        )
    
    id = uuid4()

    user_dict = {
        "id": id,
        "company_id": company_id,
        "fullname": fullname,
        "NationalID": NationalID,
        "position": position,
        "password": hash_password(password),
        "created_at": datetime.utcnow().isoformat(),
    }

    user_dict["avatar"] = save_img('avatar', avatar) if avatar else None

    await db.users.insert_one(user_dict)
    return UserOut(**user_dict)

@router.get("/protected", response_model=UserOut)
async def protected_route(current_user: UserOut = Depends(get_current_user)):
    return current_user