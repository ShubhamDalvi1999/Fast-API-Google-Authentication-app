import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # Database settings - use SQLite for local development, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./database.db"
    DATABASE_URL_UNPOOLED: Optional[str] = None
    
    # JWT settings
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/google/callback"
    
    # Supabase settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    

    
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://fast-api-google-authentication-bqox186fi.vercel.app",
        "https://*.vercel.app"
    ]
    
    # Production settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Create global settings instance
settings = Settings()

# Override settings for production
if os.environ.get("VERCEL_ENV") == "production":
    settings.ENVIRONMENT = "production"
    settings.DEBUG = False
    
    # Update redirect URI for production
    if not settings.GOOGLE_REDIRECT_URI.startswith("https://"):
        settings.GOOGLE_REDIRECT_URI = "https://fast-api-google-authentication-kwvqzt2cd.vercel.app/auth/google/callback"
    
    # Use DATABASE_URL_UNPOOLED if DATABASE_URL is not set
    if settings.DATABASE_URL == "sqlite:///./database.db" and settings.DATABASE_URL_UNPOOLED:
        settings.DATABASE_URL = settings.DATABASE_URL_UNPOOLED
else:
    # Local development: ensure we use SQLite
    if not settings.DATABASE_URL.startswith("sqlite://"):
        settings.DATABASE_URL = "sqlite:///./database.db"
