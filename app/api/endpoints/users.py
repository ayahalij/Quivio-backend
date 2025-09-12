from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserUpdate, PasswordChange
from app.services.auth_service import AuthService
import cloudinary.uploader

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

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload user avatar"""
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    # Validate file size (5MB limit for avatars)
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=413,
            detail="File size too large. Maximum 5MB allowed."
        )
    
    try:
        # Upload to Cloudinary with avatar-specific transformations
        result = cloudinary.uploader.upload(
            file_content,
            folder="quivio_avatars",
            resource_type="image",
            transformation=[
                {"width": 200, "height": 200, "crop": "fill", "gravity": "face"},
                {"quality": "auto", "fetch_format": "auto"}
            ]
        )
        
        # Update user avatar URL in database
        current_user.avatar_url = result["secure_url"]
        db.commit()
        db.refresh(current_user)
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": current_user.avatar_url
        }
        
    except Exception as e:
        print(f"Avatar upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload avatar. Please try again."
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
        "user": current_user.username,
        "avatar_url": current_user.avatar_url
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