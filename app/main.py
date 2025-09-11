from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import time

from app.core.config import settings
from app.database import engine, Base

# Import all models to register them with Base
try:
    from app.models import user, mood, diary, photo, challenge, capsule, achievement
    print("✅ All models imported successfully")
except ImportError as e:
    print(f"❌ Model import error: {e}")

# Try to import auth router
try:
    from app.api.endpoints import auth
    auth_available = True
    print("✅ Auth router imported successfully")
except ImportError as e:
    print(f"❌ Auth router import error: {e}")
    auth_available = False

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI instance
app = FastAPI(
    title="Quivio API",
    description="Personal Lifestyle Journaling Platform",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for processing time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Mount static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers if available
if auth_available:
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Quivio API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy",
        "auth_available": auth_available
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "auth_available": auth_available
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url),
            "method": request.method,
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )