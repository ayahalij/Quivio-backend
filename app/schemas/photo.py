from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime

class PhotoCreate(BaseModel):
    title: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_name: Optional[str] = None
    date: Optional[date] = None  # If not provided, will use today
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Photo title cannot be empty')
        if len(v) > 255:
            raise ValueError('Photo title must be less than 255 characters')
        return v.strip()
    
    @field_validator('location_lat')
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @field_validator('location_lng')
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v

class PhotoUpdate(BaseModel):
    title: Optional[str] = None
    location_name: Optional[str] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Photo title cannot be empty')
            if len(v) > 255:
                raise ValueError('Photo title must be less than 255 characters')
            return v.strip()
        return v

class Photo(BaseModel):
    id: int
    user_id: int
    title: str
    image_cloudinary_id: str
    image_url: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_name: Optional[str] = None
    date: date
    created_at: datetime
    
    class Config:
        from_attributes = True

class PhotoUploadResponse(BaseModel):
    message: str
    photo: Photo

class PhotoLocation(BaseModel):
    lat: float
    lng: float
    name: Optional[str] = None
    photos: list[Photo]