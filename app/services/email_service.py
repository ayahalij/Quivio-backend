# Replace your app/services/email_service.py with this enhanced version:

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from jinja2 import Template
import requests
from app.core.config import settings
import logging
import io
from PIL import Image
import base64

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_name = settings.EMAIL_FROM_NAME
        self.enabled = settings.EMAILS_ENABLED and all([
            self.smtp_host, self.smtp_user, self.smtp_password
        ])

    def download_and_resize_image(self, image_url: str, max_size: tuple = (600, 600)) -> Optional[bytes]:
        """Download and resize image for email embedding"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Open image with PIL
            img = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize while maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save as JPEG with optimization
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to download/resize image {image_url}: {e}")
            return None

    def download_video_thumbnail(self, video_url: str) -> Optional[bytes]:
        """Download first frame of video as thumbnail (simplified version)"""
        # For now, we'll just return None and use a placeholder
        # In production, you'd want to use ffmpeg or similar to extract thumbnail
        return None

    async def send_email_with_media(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        media_attachments: List[dict] = None
    ) -> bool:
        """Send email with media attachments and embedded images"""
        if not self.enabled:
            logger.warning("Email service is disabled or not configured")
            return False

        try:
            # Create main message container
            msg = MIMEMultipart('related')
            msg['From'] = f"{self.from_name} <{self.smtp_user}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject

            # Create alternative container for text/html
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg_alternative.attach(text_part)

            # Process media for embedding and attachments
            embedded_images = {}
            if media_attachments:
                for i, media in enumerate(media_attachments):
                    media_url = media.get('media_url')
                    media_type = media.get('media_type')
                    
                    if media_type == 'image':
                        # Download and resize image for embedding
                        image_data = self.download_and_resize_image(media_url)
                        if image_data:
                            # Create embedded image
                            img_cid = f"image_{i}"
                            embedded_images[media_url] = img_cid
                            
                            img_part = MIMEImage(image_data)
                            img_part.add_header('Content-ID', f'<{img_cid}>')
                            img_part.add_header('Content-Disposition', 'inline')
                            msg.attach(img_part)

            # Update HTML content to use embedded images
            if embedded_images:
                for original_url, cid in embedded_images.items():
                    html_content = html_content.replace(original_url, f'cid:{cid}')

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg_alternative.attach(html_part)

            # Add video attachments (as links, not embedded)
            if media_attachments:
                for media in media_attachments:
                    if media.get('media_type') == 'video':
                        # Videos are included as download links in HTML, not as attachments
                        # This keeps email size manageable
                        pass

            # Create secure connection and send
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email with media sent successfully to {to_emails}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email with media: {str(e)}")
            return False

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send simple email without media (backward compatibility)"""
        return await self.send_email_with_media(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            media_attachments=None
        )

    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Quivio Password</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .button { display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                .footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Reset Your Password</h1>
                    <p>Quivio - Your Personal Journal</p>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p>We received a request to reset your password for your Quivio account.</p>
                    <p>Click the button below to create a new password:</p>
                    <a href="{{ reset_url }}" class="button">Reset Password</a>
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{{ reset_url }}</p>
                    <p><strong>This link will expire in 1 hour</strong> for security reasons.</p>
                    <p>If you didn't request this password reset, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This email was sent by Quivio</p>
                    <p>Keep journaling, keep growing! 📔</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(reset_url=reset_url)
        
        return await self.send_email(
            to_emails=[email],
            subject="Reset Your Quivio Password",
            html_content=html_content,
            text_content=f"Reset your Quivio password by visiting: {reset_url}"
        )

    async def send_capsule_notification_email(
        self,
        to_emails: List[str],
        capsule_title: str,
        capsule_message: str,
        sender_name: str,
        created_date: str,
        is_personal: bool = True,
        media_attachments: List[dict] = None  # NEW: Accept media attachments
    ) -> bool:
        """Send capsule opening notification email with embedded media"""
        
        media_count = len(media_attachments) if media_attachments else 0
        
        if is_personal:
            subject = f"🎉 Your Memory Capsule '{capsule_title}' Has Opened!"
            greeting = f"Hello {sender_name}!"
            intro = "Your memory capsule has reached its opening date and is now available to view!"
        else:
            subject = f"🎁 {sender_name} Sent You a Memory Capsule!"
            greeting = "Hello!"
            intro = f"{sender_name} has shared a special memory capsule with you through Quivio!"

        # Separate images and videos
        images = [m for m in media_attachments if m.get('media_type') == 'image'] if media_attachments else []
        videos = [m for m in media_attachments if m.get('media_type') == 'video'] if media_attachments else []

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ subject }}</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .capsule-content { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50; }
                .button { display: inline-block; background: #4caf50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                .footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
                .meta { color: #666; font-size: 14px; margin-top: 10px; }
                .media-section { background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50; }
                .image-gallery { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }
                .image-item { max-width: 280px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
                .image-item img { width: 100%; height: auto; border-radius: 8px; display: block; }
                .video-links { margin: 15px 0; }
                .video-link { display: inline-block; background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }
                @media (max-width: 600px) {
                    .container { padding: 10px; }
                    .image-item { max-width: 100%; }
                    .image-gallery { flex-direction: column; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📦 Memory Capsule</h1>
                    <h2>{{ capsule_title }}</h2>
                </div>
                <div class="content">
                    <h3>{{ greeting }}</h3>
                    <p>{{ intro }}</p>
                    
                    <div class="capsule-content">
                        <h4>💌 Message:</h4>
                        <p style="font-style: italic; white-space: pre-wrap;">{{ capsule_message }}</p>
                        <div class="meta">
                            <p><strong>Created:</strong> {{ created_date }}</p>
                            {% if not is_personal %}
                            <p><strong>From:</strong> {{ sender_name }}</p>
                            {% endif %}
                        </div>
                    </div>

                    {% if has_media %}
                    <div class="media-section">
                        <h4>📷 Attached Memories</h4>
                        
                        {% if images %}
                        <h5>Photos ({{ images|length }}):</h5>
                        <div class="image-gallery">
                            {% for image in images %}
                            <div class="image-item">
                                <img src="{{ image.media_url }}" alt="Memory photo" style="max-width: 100%; height: auto;">
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        {% if videos %}
                        <h5>Videos ({{ videos|length }}):</h5>
                        <div class="video-links">
                            {% for video in videos %}
                            <a href="{{ video.media_url }}" class="video-link" target="_blank">
                                🎥 Watch Video {{ loop.index }}
                            </a>
                            {% endfor %}
                        </div>
                        <p style="color: #555; font-size: 14px;">
                            Click the links above to view the videos in your browser.
                        </p>
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    {% if is_personal %}
                    <p>You can view this capsule and all media in your Quivio timeline:</p>
                    <a href="{{ frontend_url }}/timeline" class="button">View in Quivio</a>
                    {% else %}
                    <p>This memory capsule was shared with you through Quivio, a personal journaling platform.</p>
                    <p>If you'd like to start your own journaling journey, you can create an account:</p>
                    <a href="{{ frontend_url }}" class="button">Explore Quivio</a>
                    {% endif %}
                </div>
                <div class="footer">
                    <p>This memory capsule was created with Quivio</p>
                    <p>Preserving memories, one moment at a time 🌟</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        has_media = media_count > 0
        
        template = Template(html_template)
        html_content = template.render(
            subject=subject,
            greeting=greeting,
            intro=intro,
            capsule_title=capsule_title,
            capsule_message=capsule_message,
            sender_name=sender_name,
            created_date=created_date,
            is_personal=is_personal,
            has_media=has_media,
            images=images,
            videos=videos,
            frontend_url=settings.FRONTEND_URL
        )
        
        # Create text version with media info
        media_text = ""
        if has_media:
            media_text = f"\n\nAttached Media:"
            if images:
                media_text += f"\n• {len(images)} photo(s)"
            if videos:
                media_text += f"\n• {len(videos)} video(s)"
                for i, video in enumerate(videos, 1):
                    media_text += f"\n  Video {i}: {video['media_url']}"
        
        text_content = f"""
{greeting}

{intro}

Memory Capsule: {capsule_title}

Message:
{capsule_message}{media_text}

Created: {created_date}
{'From: ' + sender_name if not is_personal else ''}

{'View in Quivio: ' + settings.FRONTEND_URL + '/timeline' if is_personal else 'Explore Quivio: ' + settings.FRONTEND_URL}
        """
        
        return await self.send_email_with_media(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            text_content=text_content.strip(),
            media_attachments=media_attachments
        )

# Create global instance
email_service = EmailService()