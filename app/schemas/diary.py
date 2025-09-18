#app/schemas/diary.py
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime

class DiaryEntryCreate(BaseModel):
    content: str
    date: Optional[date] = None  # If not provided, will use today
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Diary content cannot be empty')
        if len(v) > 5000:
            raise ValueError('Diary content must be less than 5000 characters')
        return v.strip()

class DiaryEntryUpdate(BaseModel):
    content: str
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Diary content cannot be empty')
        if len(v) > 5000:
            raise ValueError('Diary content must be less than 5000 characters')
        return v.strip()

class DiaryEntry(BaseModel):
    id: int
    user_id: int
    content: str
    word_count: int
    date: date
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DiaryStats(BaseModel):
    total_entries: int
    total_words: int
    average_words_per_entry: float
    longest_entry_words: int
    current_streak: int
    entries_this_month: int