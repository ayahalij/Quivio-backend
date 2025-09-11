from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import time

from app.core.config import settings
# We'll uncomment these as we create the routers
# from app.api.endpoints import auth, users, daily, photos, challenges, capsules, timeline

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

# Include routers (we'll uncomment these as we create them)
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/users", tags=["Users"])
# app.include_router(daily.router, prefix="/daily", tags=["Daily Entries"])
# app.include_router(photos.router, prefix="/photos", tags=["Photos"])
# app.include_router(challenges.router, prefix="/challenges", tags=["Challenges"])
# app.include_router(capsules.router, prefix="/capsules", tags=["Capsules"])
# app.include_router(timeline.router, prefix="/timeline", tags=["Timeline"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Quivio API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url),
            "method": request.method
        }
    )