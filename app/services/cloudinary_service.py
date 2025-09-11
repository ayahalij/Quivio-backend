import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import HTTPException, UploadFile
from app.core.config import settings
import uuid
from typing import Dict, Optional

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

class CloudinaryService:
    
    @staticmethod
    async def upload_image(
        file: UploadFile, 
        folder: str = "quivio",
        public_id: Optional[str] = None,
        transformation: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Upload image to Cloudinary
        
        Args:
            file: The uploaded file
            folder: Cloudinary folder (e.g., 'quivio/avatars', 'quivio/photos')
            public_id: Custom public ID (optional)
            transformation: Image transformations (optional)
        
        Returns:
            Dict with cloudinary_id and url
        """
        try:
            # Validate file type
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            # Generate unique public_id if not provided
            if not public_id:
                public_id = f"{folder}/{uuid.uuid4().hex}"
            else:
                public_id = f"{folder}/{public_id}"
            
            # Default transformations for optimization
            default_transform = {
                "quality": "auto",
                "fetch_format": "auto",
                "width": 1200,
                "height": 1200,
                "crop": "limit"
            }
            
            if transformation:
                default_transform.update(transformation)
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                folder=folder,
                transformation=default_transform,
                resource_type="image"
            )
            
            return {
                "cloudinary_id": result["public_id"],
                "url": result["secure_url"],
                "width": result.get("width", 0),
                "height": result.get("height", 0)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
    
    @staticmethod
    async def upload_avatar(file: UploadFile, user_id: int) -> Dict[str, str]:
        """Upload user avatar with specific transformations"""
        transformation = {
            "width": 200,
            "height": 200,
            "crop": "fill",
            "gravity": "face",
            "quality": "auto",
            "fetch_format": "auto"
        }
        
        return await CloudinaryService.upload_image(
            file=file,
            folder="quivio/avatars",
            public_id=f"user_{user_id}",
            transformation=transformation
        )
    
    @staticmethod
    async def upload_photo_memory(file: UploadFile, user_id: int) -> Dict[str, str]:
        """Upload photo memory with standard transformations"""
        transformation = {
            "width": 1200,
            "height": 1200,
            "crop": "limit",
            "quality": "auto",
            "fetch_format": "auto"
        }
        
        return await CloudinaryService.upload_image(
            file=file,
            folder="quivio/photos",
            transformation=transformation
        )
    
    @staticmethod
    async def upload_challenge_photo(file: UploadFile, user_id: int, challenge_id: int) -> Dict[str, str]:
        """Upload challenge completion photo"""
        transformation = {
            "width": 800,
            "height": 800,
            "crop": "limit",
            "quality": "auto",
            "fetch_format": "auto"
        }
        
        return await CloudinaryService.upload_image(
            file=file,
            folder="quivio/challenges",
            public_id=f"user_{user_id}_challenge_{challenge_id}",
            transformation=transformation
        )
    
    @staticmethod
    async def upload_capsule_media(file: UploadFile, user_id: int, capsule_id: int) -> Dict[str, str]:
        """Upload capsule media"""
        transformation = {
            "width": 1000,
            "height": 1000,
            "crop": "limit",
            "quality": "auto",
            "fetch_format": "auto"
        }
        
        return await CloudinaryService.upload_image(
            file=file,
            folder="quivio/capsules",
            public_id=f"user_{user_id}_capsule_{capsule_id}_{uuid.uuid4().hex[:8]}",
            transformation=transformation
        )
    
    @staticmethod
    async def delete_image(cloudinary_id: str) -> bool:
        """Delete image from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(cloudinary_id)
            return result.get("result") == "ok"
        except Exception as e:
            print(f"Failed to delete image {cloudinary_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_transformed_url(cloudinary_id: str, transformation: Dict) -> str:
        """Get transformed URL for existing image"""
        try:
            url, options = cloudinary.utils.cloudinary_url(
                cloudinary_id,
                **transformation
            )
            return url
        except Exception:
            return ""