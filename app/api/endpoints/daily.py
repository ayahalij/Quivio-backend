# app/api/endpoints/daily.py - FIXED VERSION
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.mood import MoodCreate, Mood
from app.schemas.diary import DiaryEntryCreate, DiaryEntry
from app.models.mood import Mood as MoodModel
from app.models.diary import DiaryEntry as DiaryModel
from datetime import date, datetime, time
from typing import Optional

router = APIRouter()

def can_edit_entry(entry_date: date) -> bool:
    """Check if entry can still be edited (before 11:59 PM on the same day)"""
    if entry_date != date.today():
        return False
    
    now = datetime.now()
    cutoff_time = datetime.combine(entry_date, time(23, 59, 59))
    return now <= cutoff_time

@router.get("/test")
async def test_daily(current_user: User = Depends(get_current_user)):
    return {
        "message": "Daily router is working!",
        "user": current_user.username,
        "current_date": date.today().isoformat()
    }

@router.post("/mood", response_model=Mood)
async def create_mood(
    mood_data: MoodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    entry_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Create or update mood entry for specified date (defaults to today)"""
    
    # Parse the date
    if entry_date:
        try:
            target_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = date.today()
    
    # Check if entry can be edited (only for today's entries)
    if target_date == date.today() and not can_edit_entry(target_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit entries after 11:59 PM"
        )
    
    # Check if mood already exists for this date
    existing_mood = db.query(MoodModel).filter(
        MoodModel.user_id == current_user.id,
        MoodModel.date == target_date
    ).first()
    
    if existing_mood:
        # Update existing mood
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
        date=target_date
    )
    db.add(new_mood)
    db.commit()
    db.refresh(new_mood)
    return new_mood

@router.post("/diary", response_model=DiaryEntry)
async def create_diary(
    diary_data: DiaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    entry_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Create or update diary entry for specified date (defaults to today)"""
    
    # Parse the date
    if entry_date:
        try:
            target_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = date.today()
    
    # Check if entry can be edited (only for today's entries)
    if target_date == date.today() and not can_edit_entry(target_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit entries after 11:59 PM"
        )
    
    word_count = len(diary_data.content.split())
    
    # Check if diary already exists for this date
    existing_diary = db.query(DiaryModel).filter(
        DiaryModel.user_id == current_user.id,
        DiaryModel.date == target_date
    ).first()
    
    if existing_diary:
        # Update existing diary
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
        date=target_date
    )
    db.add(new_diary)
    db.commit()
    db.refresh(new_diary)
    return new_diary

@router.get("/mood")
async def get_mood(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    entry_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get mood entry for specified date"""
    
    # Parse the date
    if entry_date:
        try:
            target_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = date.today()
    
    mood = db.query(MoodModel).filter(
        MoodModel.user_id == current_user.id,
        MoodModel.date == target_date
    ).first()
    
    return {
        "mood": mood,
        "date": target_date.isoformat(),
        "can_edit": can_edit_entry(target_date) if target_date == date.today() else False
    }

@router.get("/diary")
async def get_diary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    entry_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get diary entry for specified date"""
    
    # Parse the date
    if entry_date:
        try:
            target_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = date.today()
    
    diary = db.query(DiaryModel).filter(
        DiaryModel.user_id == current_user.id,
        DiaryModel.date == target_date
    ).first()
    
    return {
        "diary": diary,
        "date": target_date.isoformat(),
        "can_edit": can_edit_entry(target_date) if target_date == date.today() else False
    }

@router.get("/entry")
async def get_daily_entry(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    entry_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get complete daily entry (mood + diary + photos) for specified date"""
    
    # Parse the date
    if entry_date:
        try:
            target_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = date.today()
    
    # Get mood
    mood = db.query(MoodModel).filter(
        MoodModel.user_id == current_user.id,
        MoodModel.date == target_date
    ).first()
    
    # Get diary
    diary = db.query(DiaryModel).filter(
        DiaryModel.user_id == current_user.id,
        DiaryModel.date == target_date
    ).first()
    
    return {
        "date": target_date.isoformat(),
        "mood": mood,
        "diary": diary,
        "can_edit": can_edit_entry(target_date) if target_date == date.today() else False
    }

@router.get("/")
async def daily_root():
    return {
        "message": "Daily entries endpoints",
        "available": ["mood", "diary", "entry", "test"],
        "current_date": date.today().isoformat()
    }