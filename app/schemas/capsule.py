from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CapsuleMediaBase(BaseModel):
    media_url: str
    media_type: str  # "image" or "video"

class CapsuleMedia(CapsuleMediaBase):
    id: int
    capsule_id: int
    media_cloudinary_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CapsuleCreate(BaseModel):
    title: str
    message: str
    open_date: datetime
    is_private: bool = True
    recipient_email: Optional[str] = None

class CapsuleUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    open_date: Optional[datetime] = None

class CapsuleBase(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_private: bool
    recipient_email: Optional[str]
    open_date: datetime
    is_opened: bool
    created_at: datetime
    opened_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Original capsule schema (for backward compatibility)
class Capsule(CapsuleBase):
    pass

# Enhanced capsule schema with media
class CapsuleWithMedia(CapsuleBase):
    media: List[CapsuleMedia] = []