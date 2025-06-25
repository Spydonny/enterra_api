from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


