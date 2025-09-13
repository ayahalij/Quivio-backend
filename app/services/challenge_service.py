from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from app.models.user import User
from app.models.mood import Mood
from app.models.challenge import DailyChallenge, UserChallenge
from app.schemas.challenge import UserChallengeCreate, ChallengeResponse
from datetime import date, datetime
from typing import Optional, List
import random

class ChallengeService:
    
    @staticmethod
    def get_daily_challenge(
        db: Session, 
        user: User, 
        entry_date: date = None
    ) -> ChallengeResponse:
        """Get daily challenge based on user's mood"""
        if entry_date is None:
            entry_date = date.today()
        
        # Check if user already has a challenge for this date
        existing_challenge = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id,
            UserChallenge.date == entry_date
        ).first()
        
        if existing_challenge:
            return ChallengeResponse(
                challenge=existing_challenge.challenge,
                user_challenge=existing_challenge,
                can_complete=entry_date == date.today()
            )
        
        # Get user's mood for the date
        user_mood = db.query(Mood).filter(
            Mood.user_id == user.id,
            Mood.date == entry_date
        ).first()
        
        if not user_mood:
            # No mood set, return a neutral challenge
            mood_level = 3
        else:
            mood_level = user_mood.mood_level
        
        # Get available challenges for this mood level
        available_challenges = db.query(DailyChallenge).filter(
            DailyChallenge.mood_trigger == mood_level,
            DailyChallenge.is_active == True
        ).all()
        
        if not available_challenges:
            # Fallback to any active challenge
            available_challenges = db.query(DailyChallenge).filter(
                DailyChallenge.is_active == True
            ).all()
        
        if not available_challenges:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No challenges available"
            )
        
        # Select a random challenge
        selected_challenge = random.choice(available_challenges)
        
        # Create user challenge
        user_challenge = UserChallenge(
            user_id=user.id,
            challenge_id=selected_challenge.id,
            mood_id=user_mood.id if user_mood else None,
            date=entry_date,
            is_completed=False
        )
        
        db.add(user_challenge)
        db.commit()
        db.refresh(user_challenge)
        
        return ChallengeResponse(
            challenge=selected_challenge,
            user_challenge=user_challenge,
            can_complete=entry_date == date.today()
        )
    
    @staticmethod
    def complete_challenge(
        db: Session,
        user: User,
        challenge_id: int,
        photo_url: Optional[str] = None
    ) -> UserChallenge:
        """Complete a challenge without uploading new photo"""
        # Find the user's challenge for today
        user_challenge = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id,
            UserChallenge.challenge_id == challenge_id,
            UserChallenge.date == date.today()
        ).first()
        
        if not user_challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found for today"
            )
        
        if user_challenge.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge already completed"
            )
        
        # Mark as completed
        user_challenge.is_completed = True
        user_challenge.photo_url = photo_url
        user_challenge.completed_at = datetime.now()
        
        db.commit()
        db.refresh(user_challenge)
        
        return user_challenge
    
    @staticmethod
    async def complete_challenge_with_photo(
        db: Session,
        user: User,
        challenge_id: int,
        file: UploadFile
    ) -> UserChallenge:
        """Complete a challenge with photo upload"""
        # Import CloudinaryService here to avoid circular import
        from app.services.cloudinary_service import CloudinaryService
        
        # Find the user's challenge for today
        user_challenge = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id,
            UserChallenge.challenge_id == challenge_id,
            UserChallenge.date == date.today()
        ).first()
        
        if not user_challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found for today"
            )
        
        if user_challenge.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge already completed"
            )
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Upload to Cloudinary with challenge-specific folder
        try:
            upload_result = await CloudinaryService.upload_challenge_photo(file, user.id, challenge_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )
        
        # Mark challenge as completed and save photo data
        user_challenge.is_completed = True
        user_challenge.photo_cloudinary_id = upload_result["cloudinary_id"]
        user_challenge.photo_url = upload_result["url"]
        user_challenge.completed_at = datetime.now()
        
        db.commit()
        db.refresh(user_challenge)
        
        return user_challenge
    
    @staticmethod
    def get_user_challenge_history(
        db: Session,
        user: User,
        limit: int = 30
    ) -> List[UserChallenge]:
        """Get user's challenge history"""
        return db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id
        ).order_by(UserChallenge.date.desc()).limit(limit).all()
    
    @staticmethod
    def get_challenge_stats(
        db: Session,
        user: User
    ) -> dict:
        """Get user's challenge statistics"""
        total_challenges = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id
        ).count()
        
        completed_challenges = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id,
            UserChallenge.is_completed == True
        ).count()
        
        challenges_with_photos = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id,
            UserChallenge.is_completed == True,
            UserChallenge.photo_url.isnot(None)
        ).count()
        
        completion_rate = (completed_challenges / total_challenges * 100) if total_challenges > 0 else 0
        photo_completion_rate = (challenges_with_photos / completed_challenges * 100) if completed_challenges > 0 else 0
        
        # Calculate current streak
        current_streak = ChallengeService._calculate_current_streak(db, user)
        
        return {
            "total_challenges": total_challenges,
            "completed_challenges": completed_challenges,
            "challenges_with_photos": challenges_with_photos,
            "completion_rate": round(completion_rate, 2),
            "photo_completion_rate": round(photo_completion_rate, 2),
            "current_streak": current_streak
        }
    
    @staticmethod
    def _calculate_current_streak(db: Session, user: User) -> int:
        """Calculate current consecutive challenge completion streak"""
        # Get recent challenges in descending order
        recent_challenges = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id
        ).order_by(UserChallenge.date.desc()).limit(30).all()
        
        if not recent_challenges:
            return 0
        
        streak = 0
        for challenge in recent_challenges:
            if challenge.is_completed:
                streak += 1
            else:
                break
        
        return streak
    
    @staticmethod
    def create_sample_challenges(db: Session) -> None:
        """Create sample challenges for different mood levels"""
        sample_challenges = [
           # Mood level 1 (very sad) - uplifting challenges
            {"text": "Take 1 photo of something that makes you smile", "mood": 1, "difficulty": "easy"},
            {"text": "Capture 1 object that represents hope to you", "mood": 1, "difficulty": "medium"},
            {"text": "Photograph 1 comfort item that helps you feel safe", "mood": 1, "difficulty": "easy"},
            {"text": "Take 1 photo of light breaking through shadows", "mood": 1, "difficulty": "medium"},
            {"text": "Capture 1 positive word or quote you find around you", "mood": 1, "difficulty": "easy"},

            # Mood level 2 (sad) - gentle mood-boosting challenges
            {"text": "Take 1 photo of something beautiful in nature", "mood": 2, "difficulty": "easy"},
            {"text": "Capture 1 unique texture you notice nearby", "mood": 2, "difficulty": "easy"},
            {"text": "Photograph 1 small act of kindness you witness", "mood": 2, "difficulty": "medium"},
            {"text": "Take 1 photo of a flower or plant growing", "mood": 2, "difficulty": "easy"},
            {"text": "Capture 1 soft object that feels comforting", "mood": 2, "difficulty": "easy"},

            # Mood level 3 (neutral) - exploration challenges
            {"text": "Take 1 photo that shows a strong color in your environment", "mood": 3, "difficulty": "easy"},
            {"text": "Capture 1 photo of something old and something new together", "mood": 3, "difficulty": "medium"},
            {"text": "Photograph 1 interesting pattern or shape", "mood": 3, "difficulty": "easy"},
            {"text": "Take 1 photo of shadows forming a design", "mood": 3, "difficulty": "medium"},
            {"text": "Capture 1 everyday object but from an unusual angle", "mood": 3, "difficulty": "medium"},

            # Mood level 4 (happy) - creative challenges
            {"text": "Take 1 photo of something you feel grateful for today", "mood": 4, "difficulty": "easy"},
            {"text": "Photograph your favorite place from a unique angle", "mood": 4, "difficulty": "medium"},
            {"text": "Capture 1 photo that shows movement or action", "mood": 4, "difficulty": "medium"},
            {"text": "Take 1 photo that shows contrasting colors together", "mood": 4, "difficulty": "medium"},
            {"text": "Capture 1 playful or fun moment in your surroundings", "mood": 4, "difficulty": "easy"},

            # Mood level 5 (very happy) - adventurous challenges
            {"text": "Take 1 photo that represents your current energy", "mood": 5, "difficulty": "medium"},
            {"text": "Capture yourself in 1 photo doing something you love", "mood": 5, "difficulty": "easy"},
            {"text": "Take 1 photo that represents joy or celebration", "mood": 5, "difficulty": "hard"},
            {"text": "Capture 1 reflection of yourself in something unexpected", "mood": 5, "difficulty": "medium"},
            {"text": "Take 1 photo that feels like a memory you’ll treasure", "mood": 5, "difficulty": "medium"},

        ]
        
        for challenge_data in sample_challenges:
            # Check if challenge already exists
            existing = db.query(DailyChallenge).filter(
                DailyChallenge.challenge_text == challenge_data["text"]
            ).first()
            
            if not existing:
                challenge = DailyChallenge(
                    challenge_text=challenge_data["text"],
                    mood_trigger=challenge_data["mood"],
                    difficulty_level=challenge_data["difficulty"],
                    is_active=True
                )
                db.add(challenge)
        
        db.commit()