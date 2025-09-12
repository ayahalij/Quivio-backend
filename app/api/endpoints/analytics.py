# app/api/endpoints/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.mood import Mood
from app.models.diary import DiaryEntry
from app.models.challenge import UserChallenge
from datetime import date, datetime, timedelta
from typing import List, Dict

router = APIRouter()

@router.get("/mood-trends")
async def get_mood_trends(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mood trends for the specified number of days"""
    start_date = date.today() - timedelta(days=days)
    
    moods = db.query(Mood).filter(
        Mood.user_id == current_user.id,
        Mood.date >= start_date
    ).order_by(Mood.date).all()
    
    # Create a list for all days in range
    trends = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        mood_for_date = next((m for m in moods if m.date == current_date), None)
        
        trends.append({
            "date": current_date.isoformat(),
            "mood_level": mood_for_date.mood_level if mood_for_date else None,
            "note": mood_for_date.note if mood_for_date else None
        })
    
    return {"trends": trends}

@router.get("/mood-distribution")
async def get_mood_distribution(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mood level distribution"""
    start_date = date.today() - timedelta(days=days)
    
    distribution = db.query(
        Mood.mood_level,
        func.count(Mood.mood_level).label('count')
    ).filter(
        Mood.user_id == current_user.id,
        Mood.date >= start_date
    ).group_by(Mood.mood_level).all()
    
    return {
        "distribution": [
            {"mood_level": level, "count": count}
            for level, count in distribution
        ]
    }

@router.get("/activity-summary")
async def get_activity_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily activity summary"""
    start_date = date.today() - timedelta(days=days)
    
    # Get diary entries with word counts
    diary_entries = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == current_user.id,
        DiaryEntry.date >= start_date
    ).all()
    
    # Get completed challenges
    challenges = db.query(UserChallenge).filter(
        UserChallenge.user_id == current_user.id,
        UserChallenge.date >= start_date,
        UserChallenge.is_completed == True
    ).all()
    
    # Create activity data
    activity_data = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        diary_for_date = next((d for d in diary_entries if d.date == current_date), None)
        challenges_for_date = [c for c in challenges if c.date == current_date]
        
        activity_data.append({
            "date": current_date.isoformat(),
            "has_diary": diary_for_date is not None,
            "word_count": diary_for_date.word_count if diary_for_date else 0,
            "challenges_completed": len(challenges_for_date)
        })
    
    return {"activity": activity_data}

@router.get("/insights")
async def get_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized insights based on user data"""
    # Get recent mood data
    recent_moods = db.query(Mood).filter(
        Mood.user_id == current_user.id,
        Mood.date >= date.today() - timedelta(days=30)
    ).order_by(Mood.date.desc()).all()
    
    if not recent_moods:
        return {"insights": []}
    
    # Calculate insights
    insights = []
    
    # Average mood
    avg_mood = sum(m.mood_level for m in recent_moods) / len(recent_moods)
    insights.append({
        "type": "average_mood",
        "title": "Monthly Mood Average",
        "description": f"Your average mood this month is {avg_mood:.1f}/5"
    })
    
    # Mood trend
    if len(recent_moods) >= 7:
        recent_week = recent_moods[:7]
        previous_week = recent_moods[7:14] if len(recent_moods) >= 14 else []
        
        if previous_week:
            recent_avg = sum(m.mood_level for m in recent_week) / len(recent_week)
            previous_avg = sum(m.mood_level for m in previous_week) / len(previous_week)
            
            if recent_avg > previous_avg:
                insights.append({
                    "type": "mood_trend",
                    "title": "Improving Mood Trend",
                    "description": "Your mood has been improving over the past week"
                })
            elif recent_avg < previous_avg:
                insights.append({
                    "type": "mood_trend", 
                    "title": "Declining Mood Trend",
                    "description": "Your mood has been declining over the past week"
                })
    
    # Entry consistency
    total_days = 30
    entry_days = len(recent_moods)
    consistency = (entry_days / total_days) * 100
    
    if consistency >= 80:
        insights.append({
            "type": "consistency",
            "title": "Great Consistency",
            "description": f"You've logged your mood {consistency:.0f}% of days this month"
        })
    
    return {"insights": insights}