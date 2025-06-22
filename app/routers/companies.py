from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from pydantic import EmailStr
from uuid import UUID, uuid4
from typing import Optional
import shutil
import os

from ..models import CompanyCreate, CompanyInDB, CompanyUpdate
from ..schemas import CompanyOut
from ..auth import hash_password, get_current_user
from ..db import db


router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("/", response_model=CompanyOut)
async def create_company(
    name: str = Form(...),
    login: str = Form(...),
    password: str = Form(...),
    email: EmailStr = Form(...),
    description: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    sphere: str = Form(...),
    OKED: str = Form(...),
    avatar: Optional[UploadFile] = File(None),
):
    data = {
        "name": name,
        "login": login,
        "password": hash_password(password),
        "email": email,
        "description": description,
        "website": website,
        "location": location,
        "phoneNumber": phoneNumber,
        "OKED": OKED, 
        "sphere": sphere
    }

    if avatar:
        save_dir = "static/logos"
        os.makedirs(save_dir, exist_ok=True)
        fn = f"{uuid4().hex}_{avatar.filename}"
        path = os.path.join(save_dir, fn)
        with open(path, "wb") as buf:
            shutil.copyfileobj(avatar.file, buf)
        data["avatar"] = f"/{save_dir}/{fn}"
    else:
        data["avatar"] = File(None)

    data["id"] = str(uuid4())
    await db.company.insert_one(data)
    return CompanyInDB(**data)

@router.get("/", response_model=list[CompanyOut])
async def list_companies():
    docs = db.company.find({}, {"_id":0, "password":0})
    return [CompanyOut(**doc) async for doc in docs]

@router.get("/{company_id}", response_model=CompanyOut)
async def read_company(company_id: UUID):
    doc = await db.company.find_one({"id": company_id}, {"_id":0, "password":0})
    if not doc:
        raise HTTPException(404, "Company not found")
    return CompanyOut(**doc)

@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(company_id: UUID, payload: CompanyUpdate):
    data = payload.dict(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    res = await db.company.update_one({"id": company_id}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Company not found")
    return await read_company(company_id)

@router.delete("/{company_id}")
async def delete_company(company_id: UUID):
    res = await db.company.delete_one({"id": company_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Company not found")
    return {"detail": "Deleted"}