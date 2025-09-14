# app/schemas/capsule.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class CapsuleRecipientBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class CapsuleRecipient(CapsuleRecipientBase):
    id: int
    capsule_id: int
    email_sent: bool
    email_sent_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

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

# KEEP ORIGINAL SCHEMAS FOR BACKWARD COMPATIBILITY
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

# NEW ENHANCED SCHEMA FOR MULTIPLE RECIPIENTS
class CapsuleCreateWithRecipients(BaseModel):
    title: str
    message: str
    open_date: datetime
    is_private: bool = True
    recipient_emails: List[EmailStr] = []  # List of recipient emails
    send_to_self: bool = True  # Whether to send email to capsule creator

class CapsuleBase(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_private: bool
    recipient_email: Optional[str]  # Keep for backward compatibility
    open_date: datetime
    is_opened: bool
    created_at: datetime
    opened_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Original capsule schema (for backward compatibility)
class Capsule(CapsuleBase):
    pass

# Enhanced capsule schema with media and recipients
class CapsuleWithMediaAndRecipients(CapsuleBase):
    media: List[CapsuleMedia] = []
    recipients: List[CapsuleRecipient] = []

# Keep the old one for backward compatibility
class CapsuleWithMedia(CapsuleBase):
    media: List[CapsuleMedia] = []

class CapsuleWithRecipients(CapsuleBase):
    media: List[CapsuleMedia] = []
    recipients: List[CapsuleRecipient] = []