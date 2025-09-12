from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

# Base User Schema
class UserBase(BaseModel):
    username: str
    email: EmailStr
    bio: Optional[str] = None
    language: str = "en"
    theme_mode: str = "light"

# User Registration Schema
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    bio: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

# User Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# User Update Schema
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    language: Optional[str] = None
    theme_mode: Optional[str] = None
    avatar_url: Optional[str] = None  # Added avatar support
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username must be less than 50 characters')
        return v
    
    @validator('theme_mode')
    def validate_theme(cls, v):
        if v is not None and v not in ['light', 'dark']:
            raise ValueError('Theme mode must be either "light" or "dark"')
        return v
    
    @validator('language')
    def validate_language(cls, v):
        if v is not None and v not in ['en', 'ar']:
            raise ValueError('Language must be either "en" or "ar"')
        return v

# Password Change Schema
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# User Response Schema
class User(UserBase):
    id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# User Profile Stats Schema
class UserStats(BaseModel):
    total_entries: int
    total_photos: int
    total_challenges_completed: int
    total_capsules: int
    current_streak: int
    mood_distribution: dict
    achievements_count: int

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    user_id: Optional[str] = None