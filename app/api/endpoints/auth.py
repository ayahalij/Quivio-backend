from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, Token, TokenRefresh, User
from app.schemas.password_reset import PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse
from app.services.auth_service import AuthService
from app.core.deps import get_current_user
from app.models.user import User as UserModel
from app.models.password_reset import PasswordResetToken
from app.services.email_service import email_service
from app.core.security import get_password_hash
from app.core.config import settings
import secrets
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user = AuthService.create_user(db, user_data)
        tokens = AuthService.create_tokens(user)
        return {**tokens, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user"""
    user = AuthService.authenticate_user(db, login_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = AuthService.create_tokens(user)
    return {**tokens, "user": user}

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    try:
        result = AuthService.refresh_token(db, token_data.refresh_token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.get("/test-protected")
async def test_protected_route(
    current_user: User = Depends(get_current_user)
):
    """Test protected route"""
    return {
        "message": f"Hello {current_user.username}! This is a protected route.",
        "user_id": current_user.id,
        "status": "authenticated"
    }

# PASSWORD RESET ENDPOINTS

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset email"""
    
    # Find user by email
    user = db.query(UserModel).filter(UserModel.email == request.email.lower()).first()
    
    if not user:
        # Don't reveal if email exists or not for security
        return PasswordResetResponse(
            message="If the email exists, a password reset link has been sent.",
            success=True
        )
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Set expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    
    # Invalidate any existing tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.is_used == False
    ).update({"is_used": True})
    
    # Create new reset token
    reset_token_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    
    db.add(reset_token_record)
    db.commit()
    
    # Send email
    try:
        email_sent = await email_service.send_password_reset_email(
            email=user.email,
            reset_token=reset_token
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )
            
    except Exception as e:
        # Log error but don't reveal to user
        print(f"Failed to send password reset email: {e}")
        
    return PasswordResetResponse(
        message="If the email exists, a password reset link has been sent.",
        success=True
    )

@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    
    # Find valid token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(UserModel).filter(UserModel.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    
    # Mark token as used
    reset_token.is_used = True
    
    db.commit()
    
    return PasswordResetResponse(
        message="Password reset successfully",
        success=True
    )

@router.get("/verify-reset-token/{token}")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify if reset token is valid"""
    
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"valid": True, "message": "Token is valid"}