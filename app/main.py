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
    from app.models import user, mood, diary, photo, challenge, capsule, achievement, capsule_recipient
    print("✅ All models imported successfully")
except ImportError as e:
    print(f"❌ Model import error: {e}")

# Import all routers
try:
    from app.api.endpoints import auth
    auth_available = True
    print("✅ Auth router imported successfully")
except ImportError as e:
    print(f"❌ Auth router import error: {e}")
    auth_available = False

try:
    from app.api.endpoints import daily
    daily_available = True
    print("✅ Daily router imported successfully")
except ImportError as e:
    print(f"❌ Daily router import error: {e}")
    daily_available = False

try:
    from app.api.endpoints import challenges
    challenges_available = True
    print("✅ Challenges router imported successfully")
except ImportError as e:
    print(f"❌ Challenges router import error: {e}")
    challenges_available = False

try:
    from app.api.endpoints import timeline
    timeline_available = True
    print("✅ Timeline router imported successfully")
except ImportError as e:
    print(f"❌ Timeline router import error: {e}")
    timeline_available = False

try:
    from app.api.endpoints import users
    users_available = True
    print("✅ Users router imported successfully")
except ImportError as e:
    print(f"❌ Users router import error: {e}")
    users_available = False

try:
    from app.api.endpoints import capsules
    capsules_available = True
    print("✅ Capsules router imported successfully")
except ImportError as e:
    print(f"❌ Capsules router import error: {e}")
    capsules_available = False

try:
    from app.api.endpoints import analytics
    analytics_available = True
    print("✅ Analytics router imported successfully")
except ImportError as e:
    print(f"❌ Analytics router import error: {e}")
    analytics_available = False

try:
    from app.api.endpoints import photos
    photos_available = True
    print("✅ Photos router imported successfully")
except ImportError as e:
    print(f"❌ Photos router import error: {e}")
    photos_available = False

# Create database tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created")

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

# Include all routers
print("Registering API routes...")

if auth_available:
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    print("✅ Auth routes registered")

if daily_available:
    app.include_router(daily.router, prefix="/daily", tags=["Daily Entries"])
    print("✅ Daily routes registered")

if challenges_available:
    app.include_router(challenges.router, prefix="/challenges", tags=["Challenges"])
    print("✅ Challenges routes registered")

if timeline_available:
    app.include_router(timeline.router, prefix="/timeline", tags=["Timeline"])
    print("✅ Timeline routes registered")

if users_available:
    app.include_router(users.router, prefix="/users", tags=["Users"])
    print("✅ Users routes registered")

if capsules_available:
    app.include_router(capsules.router, prefix="/capsules", tags=["Capsules"])
    print("✅ Capsules routes registered")

if analytics_available:
    app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
    print("✅ Analytics routes registered")

if photos_available:
    app.include_router(photos.router, prefix="/photos", tags=["Photos"])
    print("✅ Photos routes registered")

print("🚀 All available routes registered successfully")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Quivio API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy",
        "available_endpoints": {
            "auth": auth_available,
            "daily": daily_available,
            "challenges": challenges_available,
            "timeline": timeline_available,
            "users": users_available,
            "capsules": capsules_available,
            "analytics": analytics_available,
            "photos": photos_available
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "available_endpoints": {
            "auth": auth_available,
            "daily": daily_available,
            "challenges": challenges_available,
            "timeline": timeline_available,
            "users": users_available,
            "capsules": capsules_available,
            "analytics": analytics_available,
            "photos": photos_available
        }
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

# Auto-initialize challenges on startup
@app.on_event("startup")
async def startup_event():
    """Initialize sample data if needed"""
    print("🔄 Running startup tasks...")
    
    try:
        from app.services.challenge_service import ChallengeService
        from app.database import get_db
        from app.models.challenge import DailyChallenge
        
        # Get database session
        db = next(get_db())
        
        # Check if challenges exist
        existing_challenges = db.query(DailyChallenge).filter(
            DailyChallenge.is_active == True
        ).count()
        
        if existing_challenges == 0:
            print("🎯 No challenges found, initializing sample challenges...")
            ChallengeService.create_sample_challenges(db)
            print("✅ Sample challenges created successfully")
        else:
            print(f"✅ Found {existing_challenges} existing challenges")
            
        db.close()
        
    except Exception as e:
        print(f"❌ Startup task failed: {e}")
    
    print("🚀 Quivio API startup complete")