# app/models/capsule.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.database import Base

class Capsule(Base):
    __tablename__ = "capsules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_private = Column(Boolean, default=True, nullable=False)
    recipient_email = Column(String(255), nullable=True)
    open_date = Column(DateTime, nullable=False)
    is_opened = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    opened_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="capsules")
    media = relationship("CapsuleMedia", back_populates="capsule", cascade="all, delete-orphan")
    recipients = relationship("CapsuleRecipient", back_populates="capsule", cascade="all, delete-orphan")
    
    @property
    def can_be_opened(self):
        """Check if the capsule can be opened based on current time"""
        if self.is_opened:
            return True
            
        current_time = datetime.now(timezone.utc)
        
        # Handle the stored open_date
        if isinstance(self.open_date, str):
            open_date = datetime.fromisoformat(self.open_date.replace('Z', '+00:00'))
        else:
            open_date = self.open_date
            
        if open_date.tzinfo is None:
            open_date = open_date.replace(tzinfo=timezone.utc)
        else:
            open_date = open_date.astimezone(timezone.utc)
            
        return current_time >= open_date

class CapsuleMedia(Base):
    __tablename__ = "capsule_media"
    
    id = Column(Integer, primary_key=True, index=True)
    capsule_id = Column(Integer, ForeignKey("capsules.id"), nullable=False)
    media_cloudinary_id = Column(String(255), nullable=False)
    media_url = Column(String(500), nullable=False)
    media_type = Column(String(50), default="image", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships - ONLY the capsule relationship
    capsule = relationship("Capsule", back_populates="media")