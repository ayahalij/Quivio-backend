from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.challenge import ChallengeResponse, UserChallenge, UserChallengeUpdate
from app.services.challenge_service import ChallengeService
from datetime import date
from typing import List, Optional

router = APIRouter()

@router.get("/daily", response_model=ChallengeResponse)
async def get_daily_challenge(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's daily challenge based on mood"""
    return ChallengeService.get_daily_challenge(db, current_user)

@router.get("/{entry_date}", response_model=ChallengeResponse) 
async def get_challenge_by_date(
    entry_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get challenge for specific date"""
    return ChallengeService.get_daily_challenge(db, current_user, entry_date)

@router.post("/complete/{challenge_id}", response_model=UserChallenge)
async def complete_challenge(
    challenge_id: int,
    update_data: UserChallengeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete a challenge without photo (just mark as done)"""
    return ChallengeService.complete_challenge(
        db, current_user, challenge_id, update_data.photo_url
    )

@router.post("/complete-with-photo/{challenge_id}", response_model=UserChallenge)
async def complete_challenge_with_photo(
    challenge_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete a challenge with photo upload"""
    return await ChallengeService.complete_challenge_with_photo(
        db, current_user, challenge_id, file
    )

@router.get("/history/me", response_model=List[UserChallenge])
async def get_my_challenge_history(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get my challenge history"""
    return ChallengeService.get_user_challenge_history(db, current_user, limit)

@router.get("/stats/me")
async def get_my_challenge_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get my challenge statistics"""
    return ChallengeService.get_challenge_stats(db, current_user)

@router.get("/test")
async def test_challenges(current_user: User = Depends(get_current_user)):
    return {
        "message": "Challenges router is working!",
        "user": current_user.username
    }

@router.post("/initialize-sample-data")
async def initialize_sample_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize sample challenges (admin function)"""
    ChallengeService.create_sample_challenges(db)
    return {"message": "Sample challenges created successfully"}