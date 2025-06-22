from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, File

class CompanyOut(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1)
    email: EmailStr
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    phone_number: Optional[str] = None
    logo: Optional[str] = None
    sphere: str
    OKED: str

    model_config = {
        "from_attributes": True  
    }

class UserOut(BaseModel):
    id: UUID
    company_id: UUID
    fullname: str
    position: str
    email: str
    avatar: Optional[str]

    model_config = {
        "from_attributes": True  
    }

class PostOut(BaseModel):
    id: UUID
    content: str
    image: Optional[str]
    sender_id: UUID
    likes: int
    timestamp: datetime

    model_config = {
        "from_attributes": True  
    }

class MessageOut(BaseModel):
    id: UUID
    content: str
    image: Optional[str]
    sender_id: UUID
    receiver_id: UUID
    timestamp: datetime
    status: str

    model_config = {
        "from_attributes": True  
    }

class ReviewOut(BaseModel):
    id: UUID
    content: str
    rating: int
    reviewer_id: UUID
    company_id: UUID
    timestamp: datetime

    model_config = {
        "from_attributes": True  
    }