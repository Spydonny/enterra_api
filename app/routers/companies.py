from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends, Query
from typing import List
from pydantic import EmailStr
from uuid import UUID, uuid4
from typing import Optional
import shutil
import os

from ..schemas import CompanyOut, CompanyCreate, CompanyInDB, CompanyUpdate
from ..utils.auth import hash_password, get_current_user
from ..db import db
from ..utils.helpers import save_img


router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("/", response_model=CompanyOut)
async def create_company(
    name: str = Form(...),
    email: EmailStr = Form(...),
    sphere: str = Form(...),
    OKED: str = Form(...),
    description: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
):
    doc = await db.company.find_one({"name": name})
    if doc:
        raise HTTPException(400, "Company with this name already exists")
    
    data = {
        "name": name,
        "email": email,
        "description": description,
        "website": website,
        "location": location,
        "phoneNumber": phoneNumber,
        "OKED": OKED, 
        "sphere": sphere
    }

    data["logo"] = save_img('logo', logo) if logo else None

    data["id"] = str(uuid4())
    await db.company.insert_one(data)
    return CompanyInDB(**data)

@router.get("/", response_model=list[CompanyOut])
async def list_companies():
    docs = db.company.find({}, {"_id":0, "password":0})
    return [CompanyOut(**doc) async for doc in docs]

@router.get("/id/{company_id}", response_model=CompanyOut)
async def read_company(company_id: UUID):
    doc = await db.company.find_one({"id": str(company_id)})
    if not doc:
        raise HTTPException(404, "Company not found")
    return CompanyOut(**doc)

@router.get("/name/{name}", response_model=CompanyOut)
async def read_company(name: str):
    doc = await db.company.find_one({"name": name})
    if not doc:
        raise HTTPException(404, "Company not found")
    return CompanyOut(**doc)

@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(company_id: UUID, payload: CompanyUpdate):
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    res = await db.company.update_one({"id": str(company_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(404, "Company not found")
    return await read_company(company_id)

@router.delete("/{company_id}")
async def delete_company(company_id: UUID):
    res = await db.company.delete_one({"id": company_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Company not found")
    return {"detail": "Deleted"}

@router.get("/search/", response_model=List[CompanyOut])
async def search_users_by_name(part: str = Query(..., min_length=1)):
    cursor = db.users.find(
        {"name": {"$regex": part, "$options": "i"}},  # нечувствительно к регистру
        {"_id": 0, "password": 0}
    )
    results = await cursor.to_list(length=50)  # ограничим количество результатов
    return [CompanyOut(**user) for user in results]
