from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.mood import MoodCreate, Mood
from app.schemas.diary import DiaryEntryCreate, DiaryEntry
from app.models.mood import Mood as MoodModel
from app.models.diary import DiaryEntry as DiaryModel
from datetime import date

router = APIRouter()

@router.get("/test")
async def test_daily(current_user: User = Depends(get_current_user)):
    return {
        "message": "Daily router is working!",
        "user": current_user.username
    }

@router.post("/mood", response_model=Mood)
async def create_mood(
    mood_data: MoodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create today's mood entry"""
    # Check if mood already exists for today
    existing_mood = db.query(MoodModel).filter(
        MoodModel.user_id == current_user.id,
        MoodModel.date == date.today()
    ).first()
    
    if existing_mood:
        existing_mood.mood_level = mood_data.mood_level
        existing_mood.note = mood_data.note
        db.commit()
        db.refresh(existing_mood)
        return existing_mood
    
    # Create new mood
    new_mood = MoodModel(
        user_id=current_user.id,
        mood_level=mood_data.mood_level,
        note=mood_data.note,
        date=date.today()
    )
    db.add(new_mood)
    db.commit()
    db.refresh(new_mood)
    return new_mood

@router.post("/diary", response_model=DiaryEntry)
async def create_diary(
    diary_data: DiaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create today's diary entry"""
    word_count = len(diary_data.content.split())
    
    # Check if diary already exists for today
    existing_diary = db.query(DiaryModel).filter(
        DiaryModel.user_id == current_user.id,
        DiaryModel.date == date.today()
    ).first()
    
    if existing_diary:
        existing_diary.content = diary_data.content
        existing_diary.word_count = word_count
        db.commit()
        db.refresh(existing_diary)
        return existing_diary
    
    # Create new diary
    new_diary = DiaryModel(
        user_id=current_user.id,
        content=diary_data.content,
        word_count=word_count,
        date=date.today()
    )
    db.add(new_diary)
    db.commit()
    db.refresh(new_diary)
    return new_diary

@router.get("/")
async def daily_root():
    return {
        "message": "Daily entries endpoints",
        "available": ["mood", "diary", "test"]
    }