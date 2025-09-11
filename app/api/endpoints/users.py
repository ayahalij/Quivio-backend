from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserUpdate, PasswordChange
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@router.put("/profile")
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    return AuthService.update_user_profile(
        db, current_user, profile_data.dict(exclude_unset=True)
    )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    AuthService.change_password(
        db, current_user, password_data.current_password, password_data.new_password
    )
    return {"message": "Password changed successfully"}

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    return {
        "total_entries": 1,
        "total_photos": 0,
        "total_challenges_completed": 0,
        "total_capsules": 0,
        "current_streak": 1,
        "mood_distribution": {"4": 1},
        "achievements_count": 0
    }

@router.get("/test")
async def test_users(current_user: User = Depends(get_current_user)):
    """Test users endpoints"""
    return {
        "message": "Users router is working!",
        "user": current_user.username
    }

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account (careful!)"""
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}