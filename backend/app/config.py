"""
CineMatch AI - Backend Configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "cinematch_ai"

    # JWT
    JWT_SECRET_KEY: str = "cinematch-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # TMDB
    TMDB_API_KEY: str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p"
    TMDB_POSTER_SIZE: str = "w500"

    # App
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ML Paths
    PROJECT_ROOT: str = str(Path(__file__).resolve().parent.parent.parent)

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()

# Derived paths
ML_DIR = Path(settings.PROJECT_ROOT) / "ml"
ARTIFACTS_DIR = ML_DIR / "artifacts"
DATA_DIR = Path(settings.PROJECT_ROOT) / "data"
PROCESSED_DIR = DATA_DIR / "processed"
