#app/services/daily_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from app.models.user import User
from app.models.mood import Mood
from app.models.diary import DiaryEntry
from app.models.photo import Photo
from app.schemas.mood import MoodCreate, MoodUpdate
from app.schemas.diary import DiaryEntryCreate, DiaryEntryUpdate
from app.schemas.photo import PhotoCreate
from app.services.cloudinary_service import CloudinaryService
from datetime import date, datetime, time
from typing import Optional, List

class DailyService:
    
    @staticmethod
    def can_edit_today_entry(entry_date: date) -> bool:
        """Check if today's entry can still be edited (before 11:59 PM)"""
        if entry_date != date.today():
            return False
        
        now = datetime.now()
        cutoff_time = datetime.combine(entry_date, time(23, 59, 59))
        return now <= cutoff_time
    
    @staticmethod
    def create_or_update_mood(
        db: Session, 
        user: User, 
        mood_data: MoodCreate
    ) -> Mood:
        """Create or update today's mood entry"""
        entry_date = mood_data.date or date.today()
        
        # Check if entry can be edited
        if not DailyService.can_edit_today_entry(entry_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit entries after 11:59 PM"
            )
        
        # Check if mood already exists for this date
        existing_mood = db.query(Mood).filter(
            Mood.user_id == user.id,
            Mood.date == entry_date
        ).first()
        
        if existing_mood:
            # Update existing mood
            existing_mood.mood_level = mood_data.mood_level
            existing_mood.note = mood_data.note
            db.commit()
            db.refresh(existing_mood)
            return existing_mood
        else:
            # Create new mood
            new_mood = Mood(
                user_id=user.id,
                mood_level=mood_data.mood_level,
                note=mood_data.note,
                date=entry_date
            )
            db.add(new_mood)
            db.commit()
            db.refresh(new_mood)
            return new_mood
    
    @staticmethod
    def create_or_update_diary(
        db: Session, 
        user: User, 
        diary_data: DiaryEntryCreate
    ) -> DiaryEntry:
        """Create or update today's diary entry"""
        entry_date = diary_data.date or date.today()
        
        # Check if entry can be edited
        if not DailyService.can_edit_today_entry(entry_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit entries after 11:59 PM"
            )
        
        # Calculate word count
        word_count = len(diary_data.content.split())
        
        # Check if diary already exists for this date
        existing_diary = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user.id,
            DiaryEntry.date == entry_date
        ).first()
        
        if existing_diary:
            # Update existing diary
            existing_diary.content = diary_data.content
            existing_diary.word_count = word_count
            db.commit()
            db.refresh(existing_diary)
            return existing_diary
        else:
            # Create new diary
            new_diary = DiaryEntry(
                user_id=user.id,
                content=diary_data.content,
                word_count=word_count,
                date=entry_date
            )
            db.add(new_diary)
            db.commit()
            db.refresh(new_diary)
            return new_diary
    
    @staticmethod
    async def upload_photo(
        db: Session,
        user: User,
        file: UploadFile,
        photo_data: PhotoCreate
    ) -> Photo:
        """Upload photo memory"""
        entry_date = photo_data.date or date.today()
        
        # Upload to Cloudinary
        try:
            upload_result = await CloudinaryService.upload_photo_memory(file, user.id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )
        
        # Create photo record
        new_photo = Photo(
            user_id=user.id,
            title=photo_data.title,
            image_cloudinary_id=upload_result["cloudinary_id"],
            image_url=upload_result["url"],
            location_lat=photo_data.location_lat,
            location_lng=photo_data.location_lng,
            location_name=photo_data.location_name,
            date=entry_date
        )
        
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)
        
        return new_photo
    
    @staticmethod
    def get_daily_entry(
        db: Session, 
        user: User, 
        entry_date: date
    ) -> dict:
        """Get all daily entries for a specific date"""
        mood = db.query(Mood).filter(
            Mood.user_id == user.id,
            Mood.date == entry_date
        ).first()
        
        diary = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user.id,
            DiaryEntry.date == entry_date
        ).first()
        
        photos = db.query(Photo).filter(
            Photo.user_id == user.id,
            Photo.date == entry_date
        ).all()
        
        return {
            "date": entry_date,
            "mood": mood,
            "diary": diary,
            "photos": photos,
            "can_edit": DailyService.can_edit_today_entry(entry_date)
        }
    
    @staticmethod
    def get_mood_by_date(
        db: Session, 
        user: User, 
        entry_date: date
    ) -> Optional[Mood]:
        """Get mood for specific date"""
        return db.query(Mood).filter(
            Mood.user_id == user.id,
            Mood.date == entry_date
        ).first()
    
    @staticmethod
    def get_diary_by_date(
        db: Session, 
        user: User, 
        entry_date: date
    ) -> Optional[DiaryEntry]:
        """Get diary entry for specific date"""
        return db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user.id,
            DiaryEntry.date == entry_date
        ).first()
    
    @staticmethod
    def get_photos_by_date(
        db: Session, 
        user: User, 
        entry_date: date
    ) -> List[Photo]:
        """Get photos for specific date"""
        return db.query(Photo).filter(
            Photo.user_id == user.id,
            Photo.date == entry_date
        ).all()
    
    @staticmethod
    def delete_photo(
        db: Session,
        user: User,
        photo_id: int
    ) -> bool:
        """Delete a photo"""
        photo = db.query(Photo).filter(
            Photo.id == photo_id,
            Photo.user_id == user.id
        ).first()
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )
        
        # Check if can edit (only for today's photos)
        if photo.date == date.today() and not DailyService.can_edit_today_entry(photo.date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete photos after 11:59 PM"
            )
        
        # Delete from Cloudinary
        CloudinaryService.delete_image(photo.image_cloudinary_id)
        
        # Delete from database
        db.delete(photo)
        db.commit()
        
        return True