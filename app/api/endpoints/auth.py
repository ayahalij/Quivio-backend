from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_auth():
    return {
        "message": "Auth router is working!",
        "endpoint": "/auth/test",
        "status": "success"
    }

@router.get("/")
async def auth_root():
    return {
        "message": "Authentication endpoints",
        "available_endpoints": [
            "/auth/test",
            "/auth/register (coming soon)",
            "/auth/login (coming soon)",
        ]
    }