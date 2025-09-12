from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.photo import Photo
from app.core.config import settings  # Import settings
from typing import List, Optional
from datetime import date
import cloudinary.uploader

router = APIRouter()

@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    title: str = Form(...),
    location_lat: Optional[float] = Form(None),
    location_lng: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a photo with optional location data"""
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_content,
            folder="quivio_photos",
            resource_type="image"
        )
        
        # Save to database
        photo = Photo(
            user_id=current_user.id,
            title=title,
            image_cloudinary_id=result["public_id"],
            image_url=result["secure_url"],
            location_lat=location_lat,
            location_lng=location_lng,
            location_name=None,
            date=date.today()
        )
        
        db.add(photo)
        db.commit()
        db.refresh(photo)
        
        return {
            "id": photo.id,
            "title": photo.title,
            "image_url": photo.image_url,
            "location_lat": photo.location_lat,
            "location_lng": photo.location_lng,
            "date": photo.date.isoformat(),
            "created_at": photo.created_at.isoformat()
        }
        
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload photo: {str(e)}"
        )

@router.get("/locations")
async def get_photo_locations(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get photos with location data for map display"""
    query = db.query(Photo).filter(
        Photo.user_id == current_user.id,
        Photo.location_lat.isnot(None),
        Photo.location_lng.isnot(None)
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
    
    return {"locations": location_groups}

@router.get("/stats")
async def get_photo_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get photo statistics"""
    total_photos = db.query(Photo).filter(Photo.user_id == current_user.id).count()
    photos_with_location = db.query(Photo).filter(
        Photo.user_id == current_user.id,
        Photo.location_lat.isnot(None)
    ).count()
    
    return {
        "total_photos": total_photos,
        "photos_with_location": photos_with_location,
        "location_percentage": (photos_with_location / total_photos * 100) if total_photos > 0 else 0
    }

@router.get("/")
async def get_user_photos(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's photos with pagination"""
    photos = db.query(Photo).filter(
        Photo.user_id == current_user.id
    ).order_by(Photo.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "photos": [
            {
                "id": photo.id,
                "title": photo.title,
                "image_url": photo.image_url,
                "location_lat": photo.location_lat,
                "location_lng": photo.location_lng,
                "date": photo.date.isoformat(),
                "created_at": photo.created_at.isoformat()
            }
            for photo in photos
        ]
    }