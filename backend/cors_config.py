"""
CORS Configuration for Henry's SmartStock AI
Handles Cross-Origin Resource Sharing for different deployment scenarios
"""

import os
from typing import List

def get_cors_origins() -> List[str]:
    """
    Get CORS origins based on environment and deployment type
    """
    # Base origins (always allowed)
    origins = [
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",  # Local development alternative
    ]
    
    # Environment-specific origins
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        # Production origins from environment variable
        cors_origins_env = os.getenv("CORS_ORIGINS", "")
        if cors_origins_env:
            env_origins = [origin.strip() for origin in cors_origins_env.split(",")]
            origins.extend(env_origins)
        
        # Common Vercel patterns
        vercel_app_name = os.getenv("VERCEL_APP_NAME", "henrys-smartstock-ai")
        origins.extend([
            f"https://{vercel_app_name}.vercel.app",
            f"https://{vercel_app_name}-*.vercel.app",  # Preview deployments
        ])
        
        # Custom domain if specified
        custom_domain = os.getenv("CUSTOM_DOMAIN")
        if custom_domain:
            origins.extend([
                f"https://{custom_domain}",
                f"https://www.{custom_domain}",
            ])
    
    elif env == "development":
        # Development origins
        origins.extend([
            "http://localhost:8080",
            "http://localhost:4173",  # Vite preview
        ])
    
    # Remove duplicates and return
    return list(set(origins))

def get_cors_config() -> dict:
    """
    Get complete CORS configuration
    """
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
        "expose_headers": [
            "X-Total-Count",
            "X-Page-Count",
            "Link",
        ],
        "max_age": 86400,  # 24 hours
    }

# Example usage in FastAPI app
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cors_config import get_cors_config

app = FastAPI()

# Add CORS middleware
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)
"""