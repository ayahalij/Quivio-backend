from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.timeline_service import TimelineService
from datetime import date
from typing import Optional

router = APIRouter()

@router.get("/calendar/{year}/{month}")
async def get_calendar_data(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calendar data for a specific month"""
    if year < 2020 or year > 2030:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year must be between 2020 and 2030"
        )
    
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    return TimelineService.get_calendar_data(db, current_user, year, month)

@router.get("/map")
async def get_map_data(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get photos with location data for map view"""
    return TimelineService.get_map_data(db, current_user, start_date, end_date)

@router.get("/search")
async def search_entries(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search through diary entries and mood notes"""
    return TimelineService.search_entries(db, current_user, q, limit)

@router.get("/entry/{entry_date}")
async def get_entry_details(
    entry_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete entry details for a specific date"""
    return TimelineService.get_entry_details(db, current_user, entry_date)

@router.get("/")
async def timeline_root():
    """Timeline endpoints information"""
    return {
        "message": "Timeline and calendar endpoints",
        "available_endpoints": [
            "/timeline/calendar/{year}/{month} - Get calendar data",
            "/timeline/map - Get map data with photo locations",
            "/timeline/search?q=term - Search diary entries",
            "/timeline/entry/{date} - Get detailed entry"
        ]
    }

@router.get("/test")
async def test_timeline(current_user: User = Depends(get_current_user)):
    """Test timeline endpoints"""
    return {
        "message": "Timeline router is working!",
        "user": current_user.username,
        "available_features": [
            "Calendar view",
            "Map with photo locations", 
            "Search functionality",
            "Entry details"
        ]
    }