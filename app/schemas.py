# schemas.py
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile, File

# --- Company Schemas ---
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    sphere: str
    OKED: str
    is_investor: bool
    type_of_registration: str
    status: str = 'free'  # default status
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    phone_number: Optional[str] = None

class CompanyCreate(CompanyBase):
    logo: Optional[UploadFile] = File(None)

class CompanyUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    description: Optional[str]
    website: Optional[str]
    location: Optional[str]
    phone_number: Optional[str]


class CompanyInDB(CompanyBase):
    id: UUID
    logo: Optional[str]

    model_config = {
        "from_attributes": True  
    }

class CompanyOut(CompanyInDB):
    pass

# --- User Schemas ---
class UserBase(BaseModel):
    company_id: UUID
    fullname: str = Field(..., min_length=1)
    NationalID: str = Field(..., min_length=12, max_length=12)
    position: str = Field(..., min_length=1)

class UserCreateBody(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    fullname: Optional[str]
    position: Optional[str]
    password: Optional[str]

class UserInDB(UserBase):
    id: UUID
    avatar: Optional[str]
    password: str 
    created_at: datetime

    model_config = {
        "from_attributes": True  
    }

class UserOut(UserBase):
    id: UUID
    avatar: Optional[str]

# --- Post Schemas ---
class PostBase(BaseModel):
    content: str = Field(..., min_length=1)

class PostCreate(PostBase):
    image: Optional[UploadFile] = File(None)

class PostUpdate(BaseModel):
    content: Optional[str]
    likes: Optional[int]

class PostInDB(PostBase):
    id: UUID
    image: Optional[str]
    sender_id: UUID
    sender_name: str
    company_id: UUID
    company_name: str
    likes: int
    timestamp: datetime

    model_config = {
        "from_attributes": True  
    }

class PostOut(PostInDB):
    pass

# --- Message Rooms Schemas ---
class MessageRoomCreate(BaseModel):
    is_group: bool = False
    name: Optional[str] = None  # только для групп
    participants: List[UUID]  # всегда хотя бы один (другой пользователь)

class MessageRoomOut(BaseModel):
    id: UUID
    is_group: bool
    name: Optional[str]
    participants: List[UUID]
    created_at: datetime

# --- Message Schemas ---
class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)

class MessageCreate(MessageBase):
    image: Optional[UploadFile] = File(None)

class MessageUpdate(BaseModel):
    content: Optional[str]
    status: Optional[str]

class MessageInDB(MessageBase):
    id: UUID
    image: Optional[str]
    sender_id: UUID
    timestamp: datetime
    status: str

    model_config = {
        "from_attributes": True  
    }

class MessageOut(MessageInDB):
    pass

# --- Review Schemas ---
class ReviewBase(BaseModel):
    content: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)

class ReviewCreate(ReviewBase):
    company_id: UUID

class ReviewUpdate(BaseModel):
    content: Optional[str]
    rating: Optional[int]

class ReviewInDB(ReviewBase):
    id: UUID
    reviewer_id: UUID
    company_id: UUID
    timestamp: datetime

    model_config = {
        "from_attributes": True  
    }

class ReviewOut(ReviewInDB):
    pass
