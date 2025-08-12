from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .routers import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


for r in [companies, users, posts, messages, reviews, auth]:
    app.include_router(r)

app_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(app_dir, "..", "static")

app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root():
    return {"message": "Welcome to Enterra API"}
