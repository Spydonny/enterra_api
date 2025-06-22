import shutil
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from uuid import uuid4
import os

from .routers import *
from .auth import oauth2_scheme, create_access_token, get_current_user, hash_password
from .db import db, get_user_by_email
from .models import TokenResponse, UserCreate
from. schemas import UserOut
from .routers.users import login as user_login

app = FastAPI()

for r in [companies, users, posts, messages, reviews]:
    app.include_router(r)

@app.post("/token", response_model=TokenResponse, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await user_login(form_data)  
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})  # or user.id
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=UserOut)
async def register(user: UserCreate = Depends()):
    # prevent duplicates
    if await get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # hash password
    user_dict = user.dict(exclude={"avatar"})
    user_dict["password"] = hash_password(user.password)
    user_dict["id"] = uuid4()

    # handle avatar upload
    if user.avatar:
        save_dir = "static/avatars"
        os.makedirs(save_dir, exist_ok=True)
        fn = f"{uuid4().hex}_{user.avatar.filename}"
        path = os.path.join(save_dir, fn)
        with open(path, "wb") as buf:
            shutil.copyfileobj(user.avatar.file, buf)
        user_dict["avatar"] = f"/{save_dir}/{fn}"
    else:
        user_dict["avatar"] = None

    # insert and return
    await db.users.insert_one(user_dict)
    return UserOut(**user_dict)


@app.get("/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

@app.get("/protected", response_model=UserOut, tags=["auth"])
async def protected_route(current_user: UserOut = Depends(get_current_user)):
    return current_user
