# project/app/routers/__init__.py

from .companies import router as companies
from .users import router as users
from .posts import router as posts
from .messages import router as messages
from .reviews import router as reviews

__all__ = [
    "companies",
    "users",
    "posts",
    "messages",
    "reviews",
]
