from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

class Capsule(BaseModel):
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