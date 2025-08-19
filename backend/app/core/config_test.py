from pydantic_settings import BaseSettings
from typing import List
import os

class TestSettings(BaseSettings):
    # Database - Use SQLite for testing
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Redis - Use fake redis for testing
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # Security
    SECRET_KEY: str = "test-secret-key-for-testing-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Environment
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env.test"

test_settings = TestSettings()