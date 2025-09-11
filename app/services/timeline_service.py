from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.user import User
from app.models.mood import Mood
from app.models.diary import DiaryEntry
from app.models.photo import Photo
from app.models.challenge import UserChallenge
from datetime import date, datetime
from typing import List, Dict, Optional
import calendar

class TimelineService:
    
    @staticmethod
    def get_calendar_data(
        db: Session, 
        user: User, 
        year: int, 
        month: int
    ) -> Dict:
        """Get calendar data for a specific month"""
        # Get first and last day of month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Get all entries for the month
        moods = db.query(Mood).filter(
            and_(
                Mood.user_id == user.id,
                Mood.date >= first_day,
                Mood.date <= last_day
            )
        ).all()
        
        diary_entries = db.query(DiaryEntry).filter(
            and_(
                DiaryEntry.user_id == user.id,
                DiaryEntry.date >= first_day,
                DiaryEntry.date <= last_day
            )
        ).all()
        
        photos = db.query(Photo).filter(
            and_(
                Photo.user_id == user.id,
                Photo.date >= first_day,
                Photo.date <= last_day
            )
        ).all()
        
        challenges = db.query(UserChallenge).filter(
            and_(
                UserChallenge.user_id == user.id,
                UserChallenge.date >= first_day,
                UserChallenge.date <= last_day
            )
        ).all()
        
        # Organize data by date
        calendar_data = {}
        
        # Process moods
        for mood in moods:
            date_str = mood.date.isoformat()
            if date_str not in calendar_data:
                calendar_data[date_str] = {}
            calendar_data[date_str]['mood'] = {
                'level': mood.mood_level,
                'note': mood.note,
                'id': mood.id
            }
        
        # Process diary entries
        for entry in diary_entries:
            date_str = entry.date.isoformat()
            if date_str not in calendar_data:
                calendar_data[date_str] = {}
            calendar_data[date_str]['diary'] = {
                'word_count': entry.word_count,
                'excerpt': entry.content[:100] + '...' if len(entry.content) > 100 else entry.content,
                'id': entry.id
            }
        
        # Process photos
        for photo in photos:
            date_str = photo.date.isoformat()
            if date_str not in calendar_data:
                calendar_data[date_str] = {}
            if 'photos' not in calendar_data[date_str]:
                calendar_data[date_str]['photos'] = []
            calendar_data[date_str]['photos'].append({
                'id': photo.id,
                'title': photo.title,
                'url': photo.image_url,
                'has_location': photo.location_lat is not None
            })
        
        # Process challenges
        for challenge in challenges:
            date_str = challenge.date.isoformat()
            if date_str not in calendar_data:
                calendar_data[date_str] = {}
            calendar_data[date_str]['challenge'] = {
                'id': challenge.id,
                'challenge_text': challenge.challenge.challenge_text if challenge.challenge else None,
                'is_completed': challenge.is_completed,
                'difficulty': challenge.challenge.difficulty_level if challenge.challenge else None
            }
        
        return {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'calendar_data': calendar_data,
            'total_days_with_entries': len(calendar_data)
        }
    
    @staticmethod
    def get_map_data(
        db: Session, 
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """Get photos with location data for map view"""
        query = db.query(Photo).filter(
            and_(
                Photo.user_id == user.id,
                Photo.location_lat.isnot(None),
                Photo.location_lng.isnot(None)
            )
        )
        
        if start_date:
            query = query.filter(Photo.date >= start_date)
        if end_date:
            query = query.filter(Photo.date <= end_date)
        
        photos = query.all()
        
        # Group photos by location (within ~100m radius)
        location_groups = []
        
        for photo in photos:
            # Find existing group within 0.001 degrees (~100m)
            found_group = False
            for group in location_groups:
                if (abs(group['lat'] - photo.location_lat) < 0.001 and 
                    abs(group['lng'] - photo.location_lng) < 0.001):
                    group['photos'].append({
                        'id': photo.id,
                        'title': photo.title,
                        'url': photo.image_url,
                        'date': photo.date.isoformat()
                    })
                    found_group = True
                    break
            
            if not found_group:
                location_groups.append({
                    'lat': photo.location_lat,
                    'lng': photo.location_lng,
                    'location_name': photo.location_name,
                    'photos': [{
                        'id': photo.id,
                        'title': photo.title,
                        'url': photo.image_url,
                        'date': photo.date.isoformat()
                    }]
                })
        
        return location_groups
    
    @staticmethod
    def search_entries(
        db: Session,
        user: User,
        search_term: str,
        limit: int = 50
    ) -> Dict:
        """Search through diary entries and mood notes"""
        search_pattern = f"%{search_term.lower()}%"
        
        # Search diary entries
        diary_results = db.query(DiaryEntry).filter(
            and_(
                DiaryEntry.user_id == user.id,
                func.lower(DiaryEntry.content).like(search_pattern)
            )
        ).order_by(DiaryEntry.date.desc()).limit(limit).all()
        
        # Search mood notes
        mood_results = db.query(Mood).filter(
            and_(
                Mood.user_id == user.id,
                Mood.note.isnot(None),
                func.lower(Mood.note).like(search_pattern)
            )
        ).order_by(Mood.date.desc()).limit(limit).all()
        
        # Combine and format results
        results = []
        
        for entry in diary_results:
            # Find excerpt with search term
            content_lower = entry.content.lower()
            search_lower = search_term.lower()
            start_idx = max(0, content_lower.find(search_lower) - 50)
            end_idx = min(len(entry.content), start_idx + 200)
            excerpt = entry.content[start_idx:end_idx]
            if start_idx > 0:
                excerpt = "..." + excerpt
            if end_idx < len(entry.content):
                excerpt = excerpt + "..."
            
            results.append({
                'type': 'diary',
                'date': entry.date.isoformat(),
                'excerpt': excerpt,
                'word_count': entry.word_count,
                'id': entry.id
            })
        
        for mood in mood_results:
            results.append({
                'type': 'mood',
                'date': mood.date.isoformat(),
                'excerpt': mood.note,
                'mood_level': mood.mood_level,
                'id': mood.id
            })
        
        # Sort by date (newest first)
        results.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'search_term': search_term,
            'total_results': len(results),
            'results': results[:limit]
        }
    
    @staticmethod
    def get_entry_details(
        db: Session,
        user: User,
        entry_date: date
    ) -> Dict:
        """Get complete entry details for a specific date"""
        mood = db.query(Mood).filter(
            and_(Mood.user_id == user.id, Mood.date == entry_date)
        ).first()
        
        diary = db.query(DiaryEntry).filter(
            and_(DiaryEntry.user_id == user.id, DiaryEntry.date == entry_date)
        ).first()
        
        photos = db.query(Photo).filter(
            and_(Photo.user_id == user.id, Photo.date == entry_date)
        ).all()
        
        challenge = db.query(UserChallenge).filter(
            and_(UserChallenge.user_id == user.id, UserChallenge.date == entry_date)
        ).first()
        
        return {
            'date': entry_date.isoformat(),
            'mood': {
                'level': mood.mood_level,
                'note': mood.note,
                'created_at': mood.created_at.isoformat()
            } if mood else None,
            'diary': {
                'content': diary.content,
                'word_count': diary.word_count,
                'created_at': diary.created_at.isoformat()
            } if diary else None,
            'photos': [{
                'id': photo.id,
                'title': photo.title,
                'url': photo.image_url,
                'location_lat': photo.location_lat,
                'location_lng': photo.location_lng,
                'location_name': photo.location_name,
                'created_at': photo.created_at.isoformat()
            } for photo in photos],
            'challenge': {
                'challenge_text': challenge.challenge.challenge_text if challenge and challenge.challenge else None,
                'is_completed': challenge.is_completed if challenge else False,
                'difficulty': challenge.challenge.difficulty_level if challenge and challenge.challenge else None,
                'photo_url': challenge.photo_url if challenge else None
            } if challenge else None
        }