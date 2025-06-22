from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = Field(..., gt=0)

    class Config:
        env_file = ".env"

settings = Settings()
