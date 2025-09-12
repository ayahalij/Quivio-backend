from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.capsule import Capsule
from app.schemas.capsule import CapsuleCreate, CapsuleUpdate, Capsule as CapsuleSchema
from datetime import datetime
from typing import List

router = APIRouter()

@router.get("/", response_model=List[CapsuleSchema])
async def get_user_capsules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all capsules for the current user"""
    capsules = db.query(Capsule).filter(
        Capsule.user_id == current_user.id
    ).order_by(Capsule.created_at.desc()).all()
    
    return capsules

@router.post("/", response_model=CapsuleSchema)
async def create_capsule(
    capsule_data: CapsuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new capsule"""
    new_capsule = Capsule(
        user_id=current_user.id,
        title=capsule_data.title,
        message=capsule_data.message,
        open_date=capsule_data.open_date,
        is_private=capsule_data.is_private,
        recipient_email=capsule_data.recipient_email
    )
    
    db.add(new_capsule)
    db.commit()
    db.refresh(new_capsule)
    
    return new_capsule

@router.get("/{capsule_id}", response_model=CapsuleSchema)
async def get_capsule(
    capsule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific capsule"""
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

@router.put("/{capsule_id}/open", response_model=CapsuleSchema)
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
    
    if capsule.open_date > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capsule cannot be opened yet"
        )
    
    capsule.is_opened = True
    capsule.opened_at = datetime.now()
    
    db.commit()
    db.refresh(capsule)
    
    return capsule