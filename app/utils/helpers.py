from fastapi import UploadFile
from uuid import uuid4, UUID
import os
import shutil

from ..db import db

def save_img(type: str, img: UploadFile) -> str:
    save_dir = f"static/{type}s"
    os.makedirs(save_dir, exist_ok=True)
    fn = f"{uuid4().hex}_{img.filename}"
    path = os.path.join(save_dir, fn)
    with open(path, "wb") as buf:
        shutil.copyfileobj(img.file, buf)

    return f"/{save_dir}/{fn}"

async def find_username(id: str) -> str:
    doc = await db.users.find_one({"id": id})
    if not doc:
        return "Unknown"
    return doc.get("name", "Unknown")

async def get_company_name(id: UUID) -> str:
    doc = await db.company.find_one({"id": str(id)})
    if not doc:
        return "Unknown"
    return doc['name'] if 'name' in doc else "Unknown"