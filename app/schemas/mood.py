from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime

class MoodCreate(BaseModel):
    mood_level: int
    note: Optional[str] = None
    date: Optional[date] = None  # If not provided, will use today
    
    @field_validator('mood_level')
    @classmethod
    def validate_mood_level(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Mood level must be between 1 and 5')
        return v
    
    @field_validator('note')
    @classmethod
    def validate_note(cls, v):
        if v and len(v) > 500:
            raise ValueError('Note must be less than 500 characters')
        return v

class MoodUpdate(BaseModel):
    mood_level: Optional[int] = None
    note: Optional[str] = None
    
    @field_validator('mood_level')
    @classmethod
    def validate_mood_level(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Mood level must be between 1 and 5')
        return v
    
    @field_validator('note')
    @classmethod
    def validate_note(cls, v):
        if v and len(v) > 500:
            raise ValueError('Note must be less than 500 characters')
        return v

class Mood(BaseModel):
    id: int
    user_id: int
    mood_level: int
    note: Optional[str] = None
    date: date
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MoodStats(BaseModel):
    average_mood: float
    mood_distribution: dict  # {1: count, 2: count, ...}
    mood_trend: str  # "improving", "declining", "stable"
    total_entries: int