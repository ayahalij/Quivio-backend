# Replace your entire app/api/endpoints/capsules.py with this enhanced version:

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.capsule import Capsule, CapsuleMedia
from app.models.capsule_recipient import CapsuleRecipient
from app.schemas.capsule import (
    CapsuleCreate, CapsuleUpdate, Capsule as CapsuleSchema, 
    CapsuleWithMedia, CapsuleCreateWithRecipients, CapsuleWithRecipients
)
from app.services.email_service import email_service
from datetime import datetime, timezone
from typing import List, Optional
import cloudinary.uploader
from threading import Thread

router = APIRouter()

@router.get("/", response_model=List[CapsuleWithMedia])
async def get_user_capsules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all capsules for the current user with media"""
    capsules = db.query(Capsule).filter(
        Capsule.user_id == current_user.id
    ).order_by(Capsule.created_at.desc()).all()
    
    return capsules

@router.post("/", response_model=CapsuleWithMedia)
async def create_capsule(
    title: str = Form(...),
    message: str = Form(...),
    open_date: str = Form(...),  # ISO string
    is_private: bool = Form(True),
    recipient_email: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new capsule with optional media files"""
    
    # Validate file count and sizes
    if len(files) > 10:  # Limit to 10 files per capsule
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per capsule"
        )
    
    # Parse open_date with proper timezone handling
    try:
        parsed_open_date = datetime.fromisoformat(open_date.replace('Z', '+00:00'))
        # Ensure it's timezone-aware (convert to UTC if needed)
        if parsed_open_date.tzinfo is None:
            parsed_open_date = parsed_open_date.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format"
        )
    
    # Create the capsule
    new_capsule = Capsule(
        user_id=current_user.id,
        title=title,
        message=message,
        open_date=parsed_open_date,
        is_private=is_private,
        recipient_email=recipient_email if recipient_email else None
    )
    
    db.add(new_capsule)
    db.commit()
    db.refresh(new_capsule)
    
    # Process media files
    for file in files:
        if file.filename:  # Skip empty file uploads
            # Validate file type
            if not file.content_type.startswith(('image/', 'video/')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} must be an image or video"
                )
            
            # Validate file size (50MB limit for videos, 10MB for images)
            file_content = await file.read()
            max_size = 50 * 1024 * 1024 if file.content_type.startswith('video/') else 10 * 1024 * 1024
            
            if len(file_content) > max_size:
                size_limit = "50MB" if file.content_type.startswith('video/') else "10MB"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds {size_limit} limit"
                )
            
            try:
                # Upload to Cloudinary
                resource_type = "video" if file.content_type.startswith('video/') else "image"
                result = cloudinary.uploader.upload(
                    file_content,
                    folder="quivio/capsules",
                    resource_type=resource_type,
                    transformation=[
                        {"quality": "auto"},
                        {"fetch_format": "auto"}
                    ] if resource_type == "image" else []
                )
                
                # Save media record
                media = CapsuleMedia(
                    capsule_id=new_capsule.id,
                    media_cloudinary_id=result["public_id"],
                    media_url=result["secure_url"],
                    media_type=resource_type
                )
                
                db.add(media)
                
            except Exception as e:
                # If upload fails, rollback the capsule creation
                db.delete(new_capsule)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload {file.filename}: {str(e)}"
                )
    
    db.commit()
    db.refresh(new_capsule)
    
    return new_capsule

@router.post("/create-with-recipients", response_model=CapsuleWithMedia)
async def create_capsule_with_recipients(
    title: str = Form(...),
    message: str = Form(...),
    open_date: str = Form(...),  # ISO string
    is_private: bool = Form(True),
    recipient_emails: str = Form(""),  # Comma-separated emails
    send_to_self: bool = Form(True),
    files: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new capsule with multiple recipients"""
    
    # Parse recipient emails
    email_list = []
    if recipient_emails.strip():
        email_list = [email.strip() for email in recipient_emails.split(",") if email.strip()]
    
    # Validate email count
    if len(email_list) > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 30 recipient emails allowed"
        )
    
    # Validate file count and sizes
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per capsule"
        )
    
    # Parse open_date
    try:
        parsed_open_date = datetime.fromisoformat(open_date.replace('Z', '+00:00'))
        if parsed_open_date.tzinfo is None:
            parsed_open_date = parsed_open_date.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format"
        )
    
    # Create the capsule
    new_capsule = Capsule(
        user_id=current_user.id,
        title=title,
        message=message,
        open_date=parsed_open_date,
        is_private=is_private
    )
    
    db.add(new_capsule)
    db.commit()
    db.refresh(new_capsule)
    
    # Add recipients
    for email in email_list:
        recipient = CapsuleRecipient(
            capsule_id=new_capsule.id,
            email=email
        )
        db.add(recipient)
    
    # Add self as recipient if requested
    if send_to_self:
        self_recipient = CapsuleRecipient(
            capsule_id=new_capsule.id,
            email=current_user.email,
            name=current_user.username
        )
        db.add(self_recipient)
    
    db.commit()
    
    # Process media files (same as existing endpoint)
    for file in files:
        if file.filename:
            if not file.content_type.startswith(('image/', 'video/')):
                continue
            
            file_content = await file.read()
            max_size = 50 * 1024 * 1024 if file.content_type.startswith('video/') else 10 * 1024 * 1024
            
            if len(file_content) > max_size:
                continue
            
            try:
                resource_type = "video" if file.content_type.startswith('video/') else "image"
                result = cloudinary.uploader.upload(
                    file_content,
                    folder="quivio/capsules",
                    resource_type=resource_type,
                    transformation=[
                        {"quality": "auto"},
                        {"fetch_format": "auto"}
                    ] if resource_type == "image" else []
                )
                
                media = CapsuleMedia(
                    capsule_id=new_capsule.id,
                    media_cloudinary_id=result["public_id"],
                    media_url=result["secure_url"],
                    media_type=resource_type
                )
                
                db.add(media)
                
            except Exception as e:
                print(f"Failed to upload {file.filename}: {str(e)}")
    
    db.commit()
    db.refresh(new_capsule)
    
    return new_capsule

@router.post("/{capsule_id}/media")
async def add_media_to_capsule(
    capsule_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add media files to an existing capsule"""
    
    # Get the capsule
    capsule = db.query(Capsule).filter(
        Capsule.id == capsule_id,
        Capsule.user_id == current_user.id
    ).first()
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capsule not found"
        )
    
    if capsule.is_opened:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add media to an opened capsule"
        )
    
    # Check current media count
    current_media_count = db.query(CapsuleMedia).filter(
        CapsuleMedia.capsule_id == capsule_id
    ).count()
    
    if current_media_count + len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per capsule"
        )
    
    uploaded_media = []
    
    for file in files:
        if file.filename:
            # Validate file type
            if not file.content_type.startswith(('image/', 'video/')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} must be an image or video"
                )
            
            # Validate file size
            file_content = await file.read()
            max_size = 50 * 1024 * 1024 if file.content_type.startswith('video/') else 10 * 1024 * 1024
            
            if len(file_content) > max_size:
                size_limit = "50MB" if file.content_type.startswith('video/') else "10MB"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds {size_limit} limit"
                )
            
            try:
                # Upload to Cloudinary
                resource_type = "video" if file.content_type.startswith('video/') else "image"
                result = cloudinary.uploader.upload(
                    file_content,
                    folder="quivio/capsules",
                    resource_type=resource_type
                )
                
                # Save media record
                media = CapsuleMedia(
                    capsule_id=capsule.id,
                    media_cloudinary_id=result["public_id"],
                    media_url=result["secure_url"],
                    media_type=resource_type
                )
                
                db.add(media)
                uploaded_media.append({
                    "id": media.id,
                    "media_url": media.media_url,
                    "media_type": media.media_type
                })
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload {file.filename}: {str(e)}"
                )
    
    db.commit()
    
    return {
        "message": f"Successfully uploaded {len(uploaded_media)} files",
        "media": uploaded_media
    }

@router.delete("/{capsule_id}/media/{media_id}")
async def delete_capsule_media(
    capsule_id: int,
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a media file from a capsule"""
    
    # Get the media
    media = db.query(CapsuleMedia).filter(
        CapsuleMedia.id == media_id,
        CapsuleMedia.capsule_id == capsule_id
    ).first()
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Check ownership
    capsule = db.query(Capsule).filter(
        Capsule.id == capsule_id,
        Capsule.user_id == current_user.id
    ).first()
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capsule not found"
        )
    
    if capsule.is_opened:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete media from an opened capsule"
        )
    
    try:
        # Delete from Cloudinary
        cloudinary.uploader.destroy(
            media.media_cloudinary_id,
            resource_type=media.media_type
        )
    except Exception as e:
        print(f"Failed to delete from Cloudinary: {e}")
        # Continue with database deletion even if Cloudinary fails
    
    # Delete from database
    db.delete(media)
    db.commit()
    
    return {"message": "Media deleted successfully"}

@router.get("/{capsule_id}", response_model=CapsuleWithMedia)
async def get_capsule(
    capsule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific capsule with media"""
    capsule = db.query(Capsule).filter(
        Capsule.id == capsule_id,
        Capsule.user_id == current_user.id
    ).first()
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capsule not found"
        )
    
    return capsule

# Background email sending function
async def send_capsule_opening_emails(capsule_id: int, db: Session):
    """Send emails to all recipients when a capsule opens with media attachments"""
    
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule or not capsule.is_opened:
        return
    
    recipients = db.query(CapsuleRecipient).filter(
        CapsuleRecipient.capsule_id == capsule_id,
        CapsuleRecipient.email_sent == False
    ).all()
    
    media_attachments = db.query(CapsuleMedia).filter(
        CapsuleMedia.capsule_id == capsule_id
    ).all()
    
    # Convert media to the format expected by email service
    media_list = []
    for media in media_attachments:
        media_list.append({
            'media_url': media.media_url,
            'media_type': media.media_type,
            'media_id': media.id
        })
    
    for recipient in recipients:
        try:
            # Determine if this is the capsule creator
            is_personal = recipient.email == capsule.user.email
            
            email_sent = await email_service.send_capsule_notification_email(
                to_emails=[recipient.email],
                capsule_title=capsule.title,
                capsule_message=capsule.message,
                sender_name=capsule.user.username,
                created_date=capsule.created_at.strftime("%B %d, %Y"),
                is_personal=is_personal,
                media_attachments=media_list  # NEW: Pass actual media data
            )
            
            if email_sent:
                recipient.email_sent = True
                recipient.email_sent_at = datetime.now(timezone.utc)
                
        except Exception as e:
            print(f"Failed to send email to {recipient.email}: {e}")
    
    db.commit()

def send_emails_background(capsule_id: int):
    """Background function to send emails"""
    from app.database import get_db
    db = next(get_db())
    try:
        import asyncio
        asyncio.run(send_capsule_opening_emails(capsule_id, db))
    finally:
        db.close()

@router.put("/{capsule_id}/open", response_model=CapsuleWithMedia)
async def open_capsule(
    capsule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Open a capsule (mark as opened)"""
    capsule = db.query(Capsule).filter(
        Capsule.id == capsule_id,
        Capsule.user_id == current_user.id
    ).first()
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capsule not found"
        )
    
    if capsule.is_opened:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capsule is already opened"
        )
    
    # FIX: Proper timezone handling for comparison
    current_time = datetime.now(timezone.utc)
    
    # Convert stored datetime to UTC for comparison
    if isinstance(capsule.open_date, str):
        # If it's a string, parse it
        open_date = datetime.fromisoformat(capsule.open_date.replace('Z', '+00:00'))
    else:
        # If it's already a datetime object
        open_date = capsule.open_date
    
    # Ensure open_date is timezone-aware and in UTC
    if open_date.tzinfo is None:
        # Treat naive datetime as UTC
        open_date = open_date.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC if it has a different timezone
        open_date = open_date.astimezone(timezone.utc)
    
    # Debug logging (remove in production)
    print(f"DEBUG - Current time (UTC): {current_time}")
    print(f"DEBUG - Open date (UTC): {open_date}")
    print(f"DEBUG - Can open? {current_time >= open_date}")
    
    # Check if the capsule can be opened (current time >= open time)
    if current_time < open_date:
        time_diff = open_date - current_time
        total_seconds = int(time_diff.total_seconds())
        
        if total_seconds > 86400:  # More than 1 day
            days = total_seconds // 86400
            remaining_time = f"{days} day{'s' if days != 1 else ''}"
        elif total_seconds > 3600:  # More than 1 hour
            hours = total_seconds // 3600
            remaining_time = f"{hours} hour{'s' if hours != 1 else ''}"
        else:  # Less than 1 hour
            minutes = max(1, total_seconds // 60)
            remaining_time = f"{minutes} minute{'s' if minutes != 1 else ''}"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capsule cannot be opened yet. {remaining_time} remaining."
        )
    
    # Mark as opened
    capsule.is_opened = True
    capsule.opened_at = current_time
    
    db.commit()
    db.refresh(capsule)
    
    # Send opening notification emails in background
    email_thread = Thread(target=send_emails_background, args=(capsule.id,))
    email_thread.start()
    
    return capsule