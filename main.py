from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# --- CONFIG ---
load_dotenv()  # This loads the .env file into environment variables

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# --- INIT ---
app = FastAPI()
client = AsyncIOMotorClient(MONGO_URI)
db = client["my_database"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
bcrypt_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- HELPERS ---
def hash_password(password: str) -> str:
    return bcrypt_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt_ctx.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await db.user.find_one({"id": user_id})
    if not user:
        raise credentials_exception
    return user

# --- SCHEMAS ---
class Company(BaseModel):
    id: Optional[str]
    name: str
    login: str
    password: str

class User(BaseModel):
    id: Optional[str]
    companyID: str
    fullname: str
    position: str
    email: EmailStr
    password: str

class Post(BaseModel):
    id: Optional[str]
    content: str
    image: Optional[str] = None
    senderID: str
    likes: int = 0
    timestamp: Optional[datetime] = None

class Message(BaseModel):
    id: Optional[str]
    content: str
    senderID: str
    receiverID: str
    timestamp: Optional[datetime] = None
    status: str = "loading"

class Review(BaseModel):
    id: Optional[str]
    content: str
    rating: int = Field(..., ge=1, le=5)
    reviewerID: str
    entityID: str            # e.g. could be a companyID or postID
    timestamp: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- AUTH ROUTES ---
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.user.find_one({"login": form_data.username}) or await db.company.find_one({"login": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user["id"]})
    return {"access_token": token, "token_type": "bearer"}

# --- CRUD ROUTES ---
# Company CRUD
@app.post("/companies", response_model=Company)
async def create_company(company: Company):
    company.id = str(uuid4())
    company.password = hash_password(company.password)
    await db.company.insert_one(company.dict())
    return company

@app.get("/companies/{company_id}", response_model=Company)
async def read_company(company_id: str):
    comp = await db.company.find_one({"id": company_id}, {"_id": 0, "password": 0})
    if not comp:
        raise HTTPException(404, "Company not found")
    return comp

@app.put("/companies/{company_id}", response_model=Company)
async def update_company(company_id: str, company: Company):
    data = company.dict(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    result = await db.company.update_one({"id": company_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(404, "Company not found")
    return await read_company(company_id)

@app.delete("/companies/{company_id}")
async def delete_company(company_id: str):
    result = await db.company.delete_one({"id": company_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Company not found")
    return {"detail": "Deleted"}

# User CRUD
@app.post("/users", response_model=User)
async def create_user(user: User):
    user.id = str(uuid4())
    user.password = hash_password(user.password)
    await db.user.insert_one(user.dict())
    return user

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: str):
    usr = await db.user.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not usr:
        raise HTTPException(404, "User not found")
    return usr

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    data = user.dict(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    result = await db.user.update_one({"id": user_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    return await read_user(user_id)

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = await db.user.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "User not found")
    return {"detail": "Deleted"}

# Post CRUD
@app.post("/posts", response_model=Post)
async def create_post(post: Post, current_user=Depends(get_current_user)):
    post.id = str(uuid4())
    post.timestamp = datetime.utcnow()
    await db.post.insert_one(post.dict())
    return post

@app.get("/posts/{post_id}", response_model=Post)
async def read_post(post_id: str):
    pst = await db.post.find_one({"id": post_id}, {"_id": 0})
    if not pst:
        raise HTTPException(404, "Post not found")
    return pst

@app.put("/posts/{post_id}", response_model=Post)
async def update_post(post_id: str, post: Post, current_user=Depends(get_current_user)):
    data = post.dict(exclude_unset=True)
    result = await db.post.update_one({"id": post_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(404, "Post not found")
    return await read_post(post_id)

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, current_user=Depends(get_current_user)):
    result = await db.post.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Post not found")
    return {"detail": "Deleted"}

# Message CRUD
@app.post("/messages", response_model=Message)
async def create_message(message: Message, current_user=Depends(get_current_user)):
    message.id = str(uuid4())
    message.timestamp = datetime.utcnow()
    await db.message.insert_one(message.dict())
    return message

@app.get("/messages/{message_id}", response_model=Message)
async def read_message(message_id: str, current_user=Depends(get_current_user)):
    msg = await db.message.find_one({"id": message_id}, {"_id": 0})
    if not msg:
        raise HTTPException(404, "Message not found")
    return msg

@app.put("/messages/{message_id}", response_model=Message)
async def update_message(message_id: str, message: Message, current_user=Depends(get_current_user)):
    data = message.dict(exclude_unset=True)
    result = await db.message.update_one({"id": message_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(404, "Message not found")
    return await read_message(message_id)

@app.delete("/messages/{message_id}")
async def delete_message(message_id: str, current_user=Depends(get_current_user)):
    result = await db.message.delete_one({"id": message_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Message not found")
    return {"detail": "Deleted"}

@app.post("/reviews", response_model=Review)
async def create_review(review: Review, current_user=Depends(get_current_user)):
    review.id = str(uuid4())
    review.timestamp = datetime.utcnow()
    await db.review.insert_one(review.dict())
    return review

@app.get("/reviews", response_model=List[Review])
async def list_reviews(limit: int = 50):
    cursor = db.review.find({}, {"_id": 0}).sort("timestamp", -1)
    return await cursor.to_list(length=limit)

@app.get("/reviews/{review_id}", response_model=Review)
async def read_review(review_id: str):
    rev = await db.review.find_one({"id": review_id}, {"_id": 0})
    if not rev:
        raise HTTPException(404, "Review not found")
    return rev

@app.put("/reviews/{review_id}", response_model=Review)
async def update_review(review_id: str, review: Review, current_user=Depends(get_current_user)):
    data = review.dict(exclude_unset=True)
    result = await db.review.update_one({"id": review_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(404, "Review not found")
    return await read_review(review_id)

@app.delete("/reviews/{review_id}")
async def delete_review(review_id: str, current_user=Depends(get_current_user)):
    result = await db.review.delete_one({"id": review_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Review not found")
    return {"detail": "Deleted"}

# --- OTHER BASIC ROUTE: increment post likes ---
@app.post("/posts/{post_id}/like", response_model=Post)
async def like_post(post_id: str, current_user=Depends(get_current_user)):
    result = await db.post.update_one({"id": post_id}, {"$inc": {"likes": 1}})
    if result.matched_count == 0:
        raise HTTPException(404, "Post not found")
    return await read_post(post_id)