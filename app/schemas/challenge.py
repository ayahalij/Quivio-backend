from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class DailyChallenge(BaseModel):
    id: int
    challenge_text: str
    mood_trigger: int
    difficulty_level: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserChallengeCreate(BaseModel):
    challenge_id: int
    photo_url: Optional[str] = None
    
class UserChallengeUpdate(BaseModel):
    is_completed: bool = True
    photo_url: Optional[str] = None

class UserChallenge(BaseModel):
    id: int
    user_id: int
    challenge_id: int
    mood_id: Optional[int] = None
    photo_cloudinary_id: Optional[str] = None
    photo_url: Optional[str] = None
    is_completed: bool
    date: date
    created_at: datetime
    completed_at: Optional[datetime] = None
    challenge: Optional[DailyChallenge] = None
    
    class Config:
        from_attributes = True

class ChallengeResponse(BaseModel):
    challenge: DailyChallenge
    user_challenge: Optional[UserChallenge] = None
    can_complete: bool