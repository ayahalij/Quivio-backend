from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.mood import Mood
from app.models.challenge import DailyChallenge, UserChallenge
from app.schemas.challenge import UserChallengeCreate, ChallengeResponse
from datetime import date
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
        """Complete a challenge"""
        # Find today's challenge
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
        user_challenge.completed_at = db.execute("SELECT CURRENT_TIMESTAMP").scalar()
        
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
        
        completion_rate = (completed_challenges / total_challenges * 100) if total_challenges > 0 else 0
        
        # Calculate current streak
        current_streak = ChallengeService._calculate_current_streak(db, user)
        
        return {
            "total_challenges": total_challenges,
            "completed_challenges": completed_challenges,
            "completion_rate": round(completion_rate, 2),
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
            {"text": "Take 3 photos of things that make you smile", "mood": 1, "difficulty": "easy"},
            {"text": "Photograph something that represents hope to you", "mood": 1, "difficulty": "medium"},
            {"text": "Capture an image of your favorite comfort item", "mood": 1, "difficulty": "easy"},
            
            # Mood level 2 (sad) - gentle mood-boosting challenges  
            {"text": "Take a photo of something beautiful in nature", "mood": 2, "difficulty": "easy"},
            {"text": "Photograph 3 different textures around you", "mood": 2, "difficulty": "easy"},
            {"text": "Capture a moment of kindness or helping others", "mood": 2, "difficulty": "medium"},
            
            # Mood level 3 (neutral) - exploration challenges
            {"text": "Take photos of 5 different colors in your environment", "mood": 3, "difficulty": "easy"},
            {"text": "Photograph something old and something new", "mood": 3, "difficulty": "medium"},
            {"text": "Capture 3 different patterns or shapes", "mood": 3, "difficulty": "easy"},
            
            # Mood level 4 (happy) - creative challenges
            {"text": "Take photos of 3 things you're grateful for today", "mood": 4, "difficulty": "easy"},
            {"text": "Photograph your favorite place from 3 different angles", "mood": 4, "difficulty": "medium"},
            {"text": "Capture a photo that shows movement or action", "mood": 4, "difficulty": "medium"},
            
            # Mood level 5 (very happy) - adventurous challenges
            {"text": "Take a photo that represents your current energy", "mood": 5, "difficulty": "medium"},
            {"text": "Photograph yourself doing something you love", "mood": 5, "difficulty": "easy"},
            {"text": "Capture 5 moments that show joy or celebration", "mood": 5, "difficulty": "hard"},
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