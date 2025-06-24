from fastapi import FastAPI

from .routers import *

app = FastAPI()

for r in [companies, users, posts, messages, reviews, auth]:
    app.include_router(r)


