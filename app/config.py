import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()  # load from .env if present

class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wellspring_ehr.db")
    secret_key: str = os.getenv("SECRET_KEY", "change_me_in_production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

settings = Settings()
