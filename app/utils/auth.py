from fastapi import Depends, HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from uuid import UUID

from ..settings import settings
from ..schemas import UserInDB  
from app.db import db

bcrypt_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def hash_password(password: str) -> str:
    return bcrypt_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt_ctx.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

async def get_user_by_NationalID(NationalID: str) -> UserInDB | None:
    data = await db.users.find_one({"NationalID": NationalID})
    if data:
        return UserInDB(**data)
    return None

async def get_companies(id: UUID) -> UserInDB | None:
    data = await db.companies.find_one({"id": id})
    if data:
        return UserInDB(**data)
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        NationalID: str = payload.get("sub")
        if NationalID is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_NationalID(NationalID)
    if user is None:
        raise credentials_exception

    return user
