from uuid import UUID, uuid4
from datetime import datetime
from fastapi.params import File
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from fastapi import UploadFile

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
