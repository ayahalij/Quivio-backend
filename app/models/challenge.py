from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class DailyChallenge(Base):
    __tablename__ = "daily_challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    challenge_text = Column(String(500), nullable=False)
    mood_trigger = Column(Integer, nullable=False)  # 1-5, which mood level triggers this challenge
    difficulty_level = Column(String(20), default="easy", nullable=False)  # easy, medium, hard
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_challenges = relationship("UserChallenge", back_populates="challenge")

class UserChallenge(Base):
    __tablename__ = "user_challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("daily_challenges.id"), nullable=False)
    mood_id = Column(Integer, ForeignKey("moods.id"), nullable=True)
    photo_cloudinary_id = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Ensure one challenge per user per day
    __table_args__ = (UniqueConstraint('user_id', 'date', name='_user_date_challenge'),)
    
    # Relationships
    user = relationship("User", back_populates="user_challenges")
    challenge = relationship("DailyChallenge", back_populates="user_challenges")
    mood = relationship("Mood", back_populates="user_challenges")