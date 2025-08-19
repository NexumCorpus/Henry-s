from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api.auth import router as auth_router
from app.api.inventory import router as inventory_router
from app.api.mobile import router as mobile_router
from app.api.websocket import router as websocket_router
from app.api.notifications import router as notifications_router
from app.services.notification_scheduler import start_notification_scheduler, stop_notification_scheduler

# Import all models to ensure they are registered
import app.models.user
import app.models.location
import app.models.supplier
import app.models.inventory
import app.models.transaction
import app.models.notification


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_notification_scheduler()
    yield
    # Shutdown
    stop_notification_scheduler()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Henry's SmartStock AI",
    description="AI-powered inventory management system for Henry's on Market",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(mobile_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(websocket_router)

@app.get("/")
async def root():
    return {"message": "Henry's SmartStock AI API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}