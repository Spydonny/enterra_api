from uuid import UUID, uuid4
from datetime import datetime
from fastapi.params import File
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from fastapi import UploadFile

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Company

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    phone_number: Optional[str] = None
    logo: Optional[str] = None
    sphere: str
    OKED: str

class CompanyInDB(CompanyCreate):
    id: UUID = Field(default_factory=uuid4)

    model_config = {
        "from_attributes": True  
    }

class CompanyUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    description: Optional[str]
    website: Optional[str]
    location: Optional[str]
    phone_number: Optional[str]
    logo: Optional[str]


# User
class UserBase(BaseModel):
    company_id: UUID
    fullname: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserCreate(UserBase):
    avatar: Optional[UploadFile] = None

class UserInDB(UserBase):
    id: UUID = Field(default_factory=uuid4)
    avatar: Optional[str] = None

    model_config = {
        "from_attributes": True  
    }

class UserUpdate(BaseModel):
    fullname: Optional[str]
    position: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    avatar: Optional[UploadFile] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Post
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1)

class PostInDB(PostCreate):
    id: UUID = Field(default_factory=uuid4)
    image: Optional[str] = None
    sender_id: UUID
    likes: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "from_attributes": True  
    }

class PostUpdate(BaseModel):
    content: Optional[str]
    likes: Optional[int]


# Message
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    receiver_id: UUID

class MessageInDB(MessageCreate):
    id: UUID = Field(default_factory=uuid4)
    sender_id: UUID
    image: Optional[str] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow())
    status: str = Field(default="loading")

    model_config = {
        "from_attributes": True  
    }

class MessageUpdate(BaseModel):
    content: Optional[str]
    status: Optional[str]


# Review
class ReviewCreate(BaseModel):
    content: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    company_id: UUID

class ReviewInDB(ReviewCreate):
    id: UUID = Field(default_factory=uuid4)
    reviewer_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "from_attributes": True  
    }

class ReviewUpdate(BaseModel):
    content: Optional[str]
    rating: Optional[int]