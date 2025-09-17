#app/services/email_service.py

import requests
from typing import List, Optional
from jinja2 import Template
from app.core.config import settings
import logging
import io
from PIL import Image
import base64

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        self.sendgrid_from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', 'quivio.dev@gmail.com')
        self.from_name = getattr(settings, 'SENDGRID_FROM_NAME', 'Quivio')
        self.enabled = settings.EMAILS_ENABLED and self.sendgrid_api_key
        self.sendgrid_url = "https://api.sendgrid.com/v3/mail/send"

    def get_base_styles(self):
        """Return base CSS styles matching Quivio login page design system"""
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Kalam:wght@300;400;700&display=swap');
            
            body { 
                font-family: 'Kalam', cursive; 
                line-height: 1.6; 
                color: #8761a7; 
                margin: 0; 
                padding: 0; 
                background-color: #fffefb;
            }
            
            .container { 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 32px 20px; 
                background-color: #fffefb;
            }
            
            .logo {
                text-align: center;
                margin-bottom: 24px;
            }
            
            .logo h1 {
                font-family: 'Kalam', cursive;
                color: #cdd475;
                font-weight: 700;
                margin: 0;
                font-size: 56px;
                line-height: 1;
            }
            
            .email-card { 
                background: #fffbef; 
                padding: 32px; 
                border-radius: 16px;
                border: 3px solid #8761a7;
                box-shadow: 0 8px 32px rgba(135, 97, 167, 0.15);
                margin: 0 auto;
            }
            
            .header-text {
                text-align: center;
                margin-bottom: 32px;
            }
            
            .header-text h2 {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-weight: 600;
                font-size: 28px;
                margin: 0 0 8px 0;
                line-height: 1.2;
            }
            
            .header-text p {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-size: 16px;
                margin: 0;
                opacity: 0.8;
            }
            
            .content-section {
                margin: 24px 0;
            }
            
            .content-section h3, .content-section h4 {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-weight: 600;
                margin: 0 0 16px 0;
            }
            
            .content-section p {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-size: 16px;
                line-height: 1.7;
                margin: 16px 0;
            }
            
            .content-section ul {
                margin: 16px 0;
                padding-left: 24px;
            }
            
            .content-section li {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-size: 16px;
                line-height: 1.7;
                margin: 8px 0;
            }
            
            .button-container {
                text-align: center;
                margin: 32px 0;
            }
            
            .button { 
                display: inline-block; 
                background-color: #cdd475; 
                color: #8761a7; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 12px; 
                font-family: 'Kalam', cursive;
                font-weight: 600;
                font-size: 18px;
                border: 2px solid #8761a7;
                box-shadow: 0 4px 15px rgba(205, 212, 117, 0.3);
                transition: all 0.3s ease;
                line-height: 1.5;
            }
            
            .button:hover {
                background-color: #dce291;
                transform: scale(1.02);
                box-shadow: 0 6px 20px rgba(205, 212, 117, 0.4);
                text-decoration: none;
                color: #8761a7;
            }
            
            .highlight-card {
                background: #dce291;
                border: 2px solid #8761a7;
                border-radius: 12px;
                padding: 24px;
                margin: 24px 0;
                text-align: center;
            }
            
            .highlight-card h3 {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-weight: 600;
                font-size: 20px;
                margin: 0 0 8px 0;
            }
            
            .highlight-card p {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-size: 16px;
                margin: 0;
                font-weight: 600;
            }
            
            .info-card {
                background: #fffefb;
                border: 2px solid #8761a7;
                border-radius: 12px;
                padding: 24px;
                margin: 24px 0;
            }
            
            .info-card h4 {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-weight: 600;
                font-size: 18px;
                margin: 0 0 16px 0;
            }
            
            .capsule-message {
                background: #fffefb;
                padding: 20px;
                border-radius: 12px;
                border: 2px solid #dce291;
                font-style: italic;
                white-space: pre-wrap;
                margin: 16px 0;
            }
            
            .meta-info {
                color: #8761a7;
                font-size: 14px;
                margin-top: 16px;
                font-family: 'Kalam', cursive;
                font-weight: 600;
                opacity: 0.8;
            }
            
            .footer { 
                text-align: center; 
                margin-top: 48px; 
                padding-top: 24px;
                border-top: 1px solid rgba(135, 97, 167, 0.2);
                color: #8761a7; 
                font-size: 14px;
                font-family: 'Kalam', cursive;
                opacity: 0.8;
            }
            
            .footer p {
                margin: 8px 0;
            }
            
            .media-section { 
                background: #f0f8f0; 
                padding: 24px; 
                border-radius: 12px; 
                margin: 24px 0; 
                border: 2px solid #8cd38f;
            }
            
            .media-section h4, .media-section h5 {
                font-family: 'Kalam', cursive;
                color: #8761a7;
                font-weight: 600;
                margin: 0 0 16px 0;
            }
            
            .image-gallery { 
                display: flex; 
                flex-wrap: wrap; 
                gap: 16px; 
                margin: 20px 0; 
                justify-content: center;
            }
            
            .image-item { 
                max-width: 280px; 
                border-radius: 12px; 
                overflow: hidden;
                border: 2px solid #8761a7;
                box-shadow: 0 4px 15px rgba(135, 97, 167, 0.2);
            }
            
            .image-item img { 
                width: 100%; 
                height: auto; 
                display: block; 
            }
            
            .video-links { 
                margin: 20px 0; 
                text-align: center;
            }
            
            .video-link { 
                display: inline-block; 
                background: #8761a7; 
                color: white; 
                padding: 12px 20px; 
                text-decoration: none; 
                border-radius: 12px; 
                margin: 8px; 
                font-family: 'Kalam', cursive;
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #8761a7;
                box-shadow: 0 4px 15px rgba(135, 97, 167, 0.3);
            }
            
            .video-link:hover {
                background: #6b4c87;
                text-decoration: none;
                color: white;
            }
            
            .mood-indicators {
                display: flex;
                justify-content: center;
                gap: 12px;
                margin: 24px 0;
                flex-wrap: wrap;
            }
            
            .mood-indicator {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 48px;
                height: 48px;
                border-radius: 50%;
                border: 3px solid;
                font-size: 28px;
                flex-shrink: 0;
            }
            
            .mood-very-sad { background: rgba(255, 107, 107, 0.2); border-color: #ff6b6b; }
            .mood-sad { background: rgba(255, 167, 38, 0.2); border-color: #ffa726; }
            .mood-neutral { background: rgba(66, 165, 245, 0.2); border-color: #42a5f5; }
            .mood-happy { background: rgba(140, 211, 143, 0.2); border-color: #8cd38f; }
            .mood-very-happy { background: rgba(71, 161, 74, 0.2); border-color: #47a14a; }
            
            .difficulty-badge {
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 700;
                display: inline-block;
                margin: 12px 0;
                font-family: 'Kalam', cursive;
                color: white;
                font-size: 14px;
            }
            
            .difficulty-easy { background: #4caf50; }
            .difficulty-medium { background: #ff9800; }
            .difficulty-hard { background: #f44336; }
            
            .challenge-text {
                font-size: 18px;
                font-weight: 600;
                font-style: italic;
                text-align: center;
                color: #8761a7;
                margin: 16px 0;
                padding: 16px;
                background: rgba(205, 212, 117, 0.1);
                border-radius: 12px;
                border: 1px solid #cdd475;
            }
            
            @media (max-width: 600px) {
                .container { 
                    padding: 20px 16px; 
                }
                .email-card { 
                    padding: 24px 20px; 
                }
                .logo h1 {
                    font-size: 40px;
                }
                .header-text h2 {
                    font-size: 24px;
                }
                .image-item { 
                    max-width: 100%; 
                }
                .image-gallery { 
                    flex-direction: column; 
                    align-items: center; 
                }
                .button { 
                    padding: 12px 20px; 
                    font-size: 16px; 
                }
                .mood-indicators {
                    gap: 8px;
                }
                .mood-indicator {
                    width: 40px;
                    height: 40px;
                    font-size: 24px;
                }
            }
        </style>
        """

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

    async def send_email_with_sendgrid(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        media_attachments: List[dict] = None
    ) -> bool:
        """Send email using SendGrid API"""
        if not self.enabled:
            logger.warning("SendGrid email service is disabled or not configured")
            return False

        try:
            # Prepare email data for SendGrid API
            email_data = {
                "personalizations": [
                    {
                        "to": [{"email": email} for email in to_emails],
                        "subject": subject
                    }
                ],
                "from": {
                    "email": self.sendgrid_from_email,
                    "name": self.from_name
                },
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ]
            }

            # Add plain text version if provided
            if text_content:
                email_data["content"].insert(0, {
                    "type": "text/plain",
                    "value": text_content
                })

            # Add attachments if provided (for media)
            if media_attachments:
                attachments = []
                for i, media in enumerate(media_attachments):
                    if media.get('media_type') == 'image':
                        image_data = self.download_and_resize_image(media.get('media_url'))
                        if image_data:
                            attachments.append({
                                "content": base64.b64encode(image_data).decode(),
                                "type": "image/jpeg",
                                "filename": f"image_{i}.jpg",
                                "disposition": "attachment"
                            })
                
                if attachments:
                    email_data["attachments"] = attachments

            # Send email via SendGrid API
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.sendgrid_url,
                json=email_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 202:
                logger.info(f"Email sent successfully via SendGrid to {to_emails}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            return False

    async def send_email_with_media(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        media_attachments: List[dict] = None
    ) -> bool:
        """Send email with media attachments using SendGrid"""
        return await self.send_email_with_sendgrid(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            media_attachments=media_attachments
        )

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send simple email without media"""
        return await self.send_email_with_sendgrid(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            media_attachments=None
        )

    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email with Quivio login page styling"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🔐 Reset Your Quivio Password</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>Quivio</h1>
                </div>
                
                <div class="email-card">
                    <div class="header-text">
                        <h2>Reset Password</h2>
                        <p>Secure your account with a new password</p>
                    </div>
                    
                    <div class="content-section">
                        <p>We received a request to reset your password for your Quivio account.</p>
                    </div>
                    
                    <div class="highlight-card">
                        <h3>Security Notice</h3>
                        <p>Click the button below to create a new password</p>
                    </div>
                    
                    <div class="button-container">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <div class="info-card">
                        <h4>Important Information</h4>
                        <ul>
                            <li><strong>This link will expire in 1 hour</strong> for your security</li>
                            <li>If you didn't request this reset, you can safely ignore this email</li>
                            <li>For security reasons, please don't share this link with anyone</li>
                        </ul>
                        
                        <div class="meta-info">
                            <p style="word-break: break-all; font-size: 12px;">
                                Reset link: {reset_url}
                            </p>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This email was sent by Quivio</p>
                    <p>Keep journaling, keep growing!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Hello!

We received a request to reset your password for your Quivio account.

Reset your password by visiting: {reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, you can safely ignore this email.

---
Quivio - Keep journaling, keep growing!
        """
        
        return await self.send_email(
            to_emails=[email],
            subject="Reset Your Quivio Password",
            html_content=html_template,
            text_content=text_content
        )

    async def send_welcome_email(self, email: str, username: str) -> bool:
        """Send welcome email to new users"""
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Quivio!</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>Quivio</h1>
                </div>
                
                <div class="email-card">
                    <div class="header-text">
                        <h2>Welcome to Quivio!</h2>
                        <p>Your personal journaling journey begins here</p>
                    </div>
                    
                    <div class="content-section">
                        <p>Hello {username}!</p>
                        <p>Welcome to Quivio, where your thoughts, memories, and moments come to life!</p>
                    </div>
                    
                    <div class="highlight-card">
                        <h3>Your account is ready to use!</h3>
                        <p>Start capturing your daily journey today</p>
                    </div>
                    
                    <div class="button-container">
                        <a href="{settings.FRONTEND_URL}/dashboard" class="button">Start Journaling</a>
                    </div>
                    
                    <div class="info-card">
                        <h4>Get Started</h4>
                        <ul>
                            <li><strong>Track your mood</strong> - Record how you're feeling each day</li>
                            <li><strong>Write diary entries</strong> - Capture your thoughts and experiences</li>
                            <li><strong>Add photo memories</strong> - Preserve special moments with pictures</li>
                            <li><strong>Create memory capsules</strong> - Send messages to your future self</li>
                            <li><strong>Take on challenges</strong> - Complete daily photography challenges</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Happy journaling from the Quivio team!</p>
                    <p>Preserving memories, one moment at a time</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Welcome to Quivio, {username}!

Your personal journaling journey begins here.

Get Started:
• Track your mood daily
• Write diary entries  
• Add photo memories
• Create memory capsules
• Take on challenges

Start journaling: {settings.FRONTEND_URL}/dashboard

Happy journaling from the Quivio team!
        """
        
        return await self.send_email(
            to_emails=[email],
            subject="Welcome to Quivio - Start Your Journaling Journey!",
            html_content=html_template,
            text_content=text_content
        )

    async def send_capsule_notification_email(
        self,
        to_emails: List[str],
        capsule_title: str,
        capsule_message: str,
        sender_name: str,
        created_date: str,
        is_personal: bool = True,
        media_attachments: List[dict] = None
    ) -> bool:
        """Send capsule opening notification email"""
        
        media_count = len(media_attachments) if media_attachments else 0
        
        if is_personal:
            subject = f"Your Memory Capsule '{capsule_title}' Has Opened!"
            greeting = f"Hello {sender_name}!"
            intro = "Your memory capsule has reached its opening date and is now available to view!"
        else:
            subject = f"{sender_name} Sent You a Memory Capsule!"
            greeting = "Hello!"
            intro = f"{sender_name} has shared a special memory capsule with you through Quivio!"

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>Quivio</h1>
                </div>
                
                <div class="email-card">
                    <div class="header-text">
                        <h2>Memory Capsule</h2>
                        <p>A special message from the past</p>
                    </div>
                    
                    <div class="content-section">
                        <p>{greeting}</p>
                        <p>{intro}</p>
                    </div>
                    
                    <div class="highlight-card">
                        <h3>{capsule_title}</h3>
                        <p>Your memory capsule is now open</p>
                    </div>
                    
                    <div class="info-card">
                        <h4>Your Message:</h4>
                        <div class="capsule-message">
                            {capsule_message}
                        </div>
                        
                        <div class="meta-info">
                            <p><strong>Created:</strong> {created_date}</p>
                        </div>
                    </div>
                    
                    <div class="button-container">
                        <a href="{settings.FRONTEND_URL}/timeline" class="button">View in Quivio Timeline</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
{greeting}

{intro}

Memory Capsule: {capsule_title}

Message:
{capsule_message}

Created: {created_date}

View in Quivio: {settings.FRONTEND_URL}/timeline

---
This memory capsule was created with Quivio
        """
        
        return await self.send_email_with_media(
            to_emails=to_emails,
            subject=subject,
            html_content=html_template,
            text_content=text_content.strip(),
            media_attachments=media_attachments
        )

# Create global instance
email_service = EmailService()