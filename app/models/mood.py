from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Mood(Base):
    __tablename__ = "moods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood_level = Column(Integer, nullable=False)  # 1-5 (very sad to very happy)
    note = Column(Text, nullable=True)  # "Why are you feeling this way?"
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Ensure one mood per user per day
    __table_args__ = (UniqueConstraint('user_id', 'date', name='_user_date_mood'),)
    
    # Relationships
    user = relationship("User", back_populates="moods")
    user_challenges = relationship("UserChallenge", back_populates="mood")