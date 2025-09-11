from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Capsule(Base):
    __tablename__ = "capsules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_private = Column(Boolean, default=True, nullable=False)
    recipient_email = Column(String(255), nullable=True)
    open_date = Column(DateTime(timezone=True), nullable=False)
    is_opened = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    opened_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="capsules")
    media = relationship("CapsuleMedia", back_populates="capsule", cascade="all, delete-orphan")

class CapsuleMedia(Base):
    __tablename__ = "capsule_media"
    
    id = Column(Integer, primary_key=True, index=True)
    capsule_id = Column(Integer, ForeignKey("capsules.id"), nullable=False)
    media_cloudinary_id = Column(String(255), nullable=False)
    media_url = Column(String(500), nullable=False)
    media_type = Column(String(50), default="image", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    capsule = relationship("Capsule", back_populates="media")