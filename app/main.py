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

# Try to import daily router
try:
    from app.api.endpoints import daily
    daily_available = True
    print("✅ Daily router imported successfully")
except ImportError as e:
    print(f"❌ Daily router import error: {e}")
    daily_available = False

# Try to import challenges router
try:
    from app.api.endpoints import challenges
    challenges_available = True
    print("✅ Challenges router imported successfully")
except ImportError as e:
    print(f"❌ Challenges router import error: {e}")
    challenges_available = False

# Try to import timeline router
try:
    from app.api.endpoints import timeline
    timeline_available = True
    print("✅ Timeline router imported successfully")
except ImportError as e:
    print(f"❌ Timeline router import error: {e}")
    timeline_available = False

# Try to import users router
try:
    from app.api.endpoints import users
    users_available = True
    print("✅ Users router imported successfully")
except ImportError as e:
    print(f"❌ Users router import error: {e}")
    users_available = False

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

if daily_available:
    app.include_router(daily.router, prefix="/daily", tags=["Daily Entries"])

if challenges_available:
    app.include_router(challenges.router, prefix="/challenges", tags=["Challenges"])

if timeline_available:
    app.include_router(timeline.router, prefix="/timeline", tags=["Timeline"])

if users_available:
    app.include_router(users.router, prefix="/users", tags=["Users"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Quivio API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy",
        "auth_available": auth_available,
        "daily_available": daily_available,
        "challenges_available": challenges_available
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "auth_available": auth_available,
        "daily_available": daily_available,
        "challenges_available": challenges_available
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