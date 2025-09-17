#app/services/email_service.py

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
            try:
                if self.smtp_port == 465:
                    # Use SSL from the start for port 465
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                        server.login(self.smtp_user, self.smtp_password)
                        server.send_message(msg)
                else:
                    # Use STARTTLS for port 587
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                        server.starttls(context=context)
                        server.login(self.smtp_user, self.smtp_password)
                        server.send_message(msg)
            except Exception as smtp_error:
                logger.error(f"SMTP Error Details: {type(smtp_error).__name__}: {str(smtp_error)}")
                raise smtp_error

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
        """Send welcome email to new users with Quivio login page styling"""
        
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
                    
                    <div class="info-card">
                        <h4>Tips for Success</h4>
                        <ul>
                            <li>Make journaling a daily habit - even a few minutes makes a difference</li>
                            <li>Be honest with yourself - this is your safe space</li>
                            <li>Use the mood tracker to identify patterns in your emotional well-being</li>
                            <li>Create memory capsules for future milestones or just to surprise yourself</li>
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
Preserving memories, one moment at a time.
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
        """Send capsule opening notification email with Quivio styling and embedded media"""
        
        media_count = len(media_attachments) if media_attachments else 0
        
        if is_personal:
            subject = f"Your Memory Capsule '{capsule_title}' Has Opened!"
            greeting = f"Hello {sender_name}!"
            intro = "Your memory capsule has reached its opening date and is now available to view!"
        else:
            subject = f"{sender_name} Sent You a Memory Capsule!"
            greeting = "Hello!"
            intro = f"{sender_name} has shared a special memory capsule with you through Quivio!"

        # Separate images and videos
        images = [m for m in media_attachments if m.get('media_type') == 'image'] if media_attachments else []
        videos = [m for m in media_attachments if m.get('media_type') == 'video'] if media_attachments else []

        # Build media sections separately to avoid f-string emoji issues
        photos_section = ""
        if images:
            image_items = ''.join([f'<div class="image-item"><img src="{image["media_url"]}" alt="Memory photo"></div>' for image in images])
            photos_section = f"""
            <h5 style="color: #8761a7; font-family: 'Kalam', cursive;">Photos ({len(images)}):</h5>
            <div class="image-gallery">
                {image_items}
            </div>
            """
        
        videos_section = ""
        if videos:
            video_links = ''.join([f'<a href="{video["media_url"]}" class="video-link" target="_blank">Watch Video {i+1}</a>' for i, video in enumerate(videos)])
            videos_section = f"""
            <h5 style="color: #8761a7; font-family: 'Kalam', cursive;">Videos ({len(videos)}):</h5>
            <div class="video-links">
                {video_links}
            </div>
            <p style="color: #8761a7; font-size: 14px; text-align: center; font-family: 'Kalam', cursive;">
                Click the links above to view the videos in your browser.
            </p>
            """
        
        media_section_html = ""
        if media_count > 0:
            media_section_html = f"""
            <div class="media-section">
                <h4>Attached Memories ({media_count})</h4>
                {photos_section}
                {videos_section}
            </div>
            """
        
        about_section = ""
        if not is_personal:
            about_section = """
            <div class="info-card">
                <h4>About Quivio</h4>
                <p>This memory capsule was shared with you through Quivio, a personal journaling platform that helps people preserve memories, track moods, and create meaningful connections with their future selves.</p>
                <p>Ready to start your own journaling journey? Join thousands of others who are already preserving their precious moments!</p>
            </div>
            """
        
        action_button = f'<a href="{settings.FRONTEND_URL}/timeline" class="button">View in Quivio Timeline</a>' if is_personal else f'<a href="{settings.FRONTEND_URL}" class="button">Explore Quivio</a>'
        
        from_info = f'<p><strong>From:</strong> {sender_name}</p>' if not is_personal else ''
        
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
                            {from_info}
                        </div>
                    </div>

                    {media_section_html}
                    
                    <div class="button-container">
                        {action_button}
                    </div>
                    
                    {about_section}
                </div>
                
            </div>
        </body>
        </html>
        """
        
        # Create text version with media info
        media_text = ""
        if media_count > 0:
            media_text = f"\n\nAttached Media ({media_count}):"
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

---
This memory capsule was created with Quivio
Preserving memories, one moment at a time
        """
        
        return await self.send_email_with_media(
            to_emails=to_emails,
            subject=subject,
            html_content=html_template,
            text_content=text_content.strip(),
            media_attachments=media_attachments
        )

    async def send_mood_reminder_email(self, email: str, username: str, days_missed: int) -> bool:
        """Send mood tracking reminder email with login page styling"""
        
        # Different messaging based on days missed
        if days_missed == 1:
            message = "We noticed you missed tracking your mood yesterday."
        elif days_missed <= 3:
            message = f"It's been {days_missed} days since your last mood entry."
        else:
            message = f"We miss you! It's been {days_missed} days since your last mood check-in."

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>How are you feeling today?</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>Quivio</h1>
                </div>
                
                <div class="email-card">
                    <div class="header-text">
                        <h2>How are you feeling?</h2>
                        <p>Your mood check-in reminder</p>
                    </div>
                    
                    <div class="content-section">
                        <p>Hello {username}!</p>
                        <p>{message} Your emotional wellbeing matters, and tracking your mood helps you understand patterns and growth over time.</p>
                    </div>
                    
                    <div class="highlight-card">
                        <h3>Take a moment to check in with yourself</h3>
                        <p>Self-awareness is the first step to emotional growth</p>
                    </div>
                    
                    <div class="mood-indicators">
                        <div class="mood-indicator mood-very-sad">😞</div>
                        <div class="mood-indicator mood-sad">😕</div>
                        <div class="mood-indicator mood-neutral">😐</div>
                        <div class="mood-indicator mood-happy">😊</div>
                        <div class="mood-indicator mood-very-happy">😄</div>
                    </div>
                    
                    <div class="button-container">
                        <a href="{settings.FRONTEND_URL}/dashboard" class="button">Track My Mood Now</a>
                    </div>
                    
                    <div class="info-card">
                        <h4>Why track your mood?</h4>
                        <ul>
                            <li><strong>Identify patterns</strong> - Notice what affects your emotional state</li>
                            <li><strong>Celebrate progress</strong> - See how far you've come</li>
                            <li><strong>Build awareness</strong> - Develop emotional intelligence</li>
                            <li><strong>Track wellness</strong> - Monitor your mental health journey</li>
                        </ul>
                    </div>
                    
                    <div class="info-card">
                        <h4>Quick Tip</h4>
                        <p>Try to check in with your mood at the same time each day - many users find evening reflection works best, but choose what feels right for you!</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Taking care of your mental health, one day at a time</p>
                    <p>With love from the Quivio team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Hello {username}!

{message} Your emotional wellbeing matters, and tracking your mood helps you understand patterns and growth over time.

Why track your mood?
• Identify patterns - Notice what affects your emotional state
• Celebrate progress - See how far you've come  
• Build awareness - Develop emotional intelligence
• Track wellness - Monitor your mental health journey

Track your mood now: {settings.FRONTEND_URL}/dashboard

Quick Tip: Try to check in with your mood at the same time each day - many users find evening reflection works best, but choose what feels right for you!

---
Taking care of your mental health, one day at a time
With love from the Quivio team
        """
        
        return await self.send_email(
            to_emails=[email],
            subject=f"How are you feeling today, {username}?",
            html_content=html_template,
            text_content=text_content
        )

    async def send_daily_challenge_email(self, email: str, username: str, challenge_text: str, difficulty: str) -> bool:
        """Send daily photography challenge email with login page styling"""
        
        difficulty_class = f"difficulty-{difficulty.lower()}"

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Today's Photography Challenge</title>
            {self.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>Quivio</h1>
                </div>
                
                <div class="email-card">
                    <div class="header-text">
                        <h2>Daily Challenge</h2>
                        <p>Your photography challenge awaits!</p>
                    </div>
                    
                    <div class="content-section">
                        <p>Hello {username}!</p>
                        <p>Ready for today's creative challenge? We've prepared something special to help you see the world through a new lens!</p>
                    </div>
                    
                    <div class="highlight-card">
                        <span class="difficulty-badge {difficulty_class}">{difficulty.upper()} CHALLENGE</span>
                        <h3>Today's Mission:</h3>
                        <div class="challenge-text">"{challenge_text}"</div>
                    </div>
                    
                    <div class="button-container">
                        <a href="{settings.FRONTEND_URL}/dashboard" class="button">Complete Challenge</a>
                    </div>
                    
                    <div class="info-card">
                        <h4>Challenge Tips</h4>
                        <ul>
                            <li><strong>Take your time</strong> - Great photos come from patience and observation</li>
                            <li><strong>Think creatively</strong> - Look for unique angles and perspectives</li>
                            <li><strong>Pay attention to light</strong> - Natural lighting often works best</li>
                            <li><strong>Tell a story</strong> - What emotion or message does your photo convey?</li>
                            <li><strong>Have fun!</strong> - Challenges are about growth and creativity, not perfection</li>
                        </ul>
                    </div>
                    
                    <div class="info-card">
                        <h4>Why Take Challenges?</h4>
                        <p>Photography challenges help you develop your creative eye, build consistency in your practice, and create a diverse collection of memories. Each challenge is designed to push your boundaries while keeping the experience enjoyable and rewarding.</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Capturing life's beauty, one challenge at a time</p>
                    <p>Happy shooting from the Quivio team!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Hello {username}!

Ready for today's creative challenge? We've prepared something special to help you see the world through a new lens!

{difficulty.upper()} CHALLENGE
Today's Mission: "{challenge_text}"

Challenge Tips:
• Take your time - Great photos come from patience and observation
• Think creatively - Look for unique angles and perspectives  
• Pay attention to light - Natural lighting often works best
• Tell a story - What emotion or message does your photo convey?
• Have fun! - Challenges are about growth and creativity, not perfection

Complete your challenge: {settings.FRONTEND_URL}/dashboard

Why Take Challenges?
Photography challenges help you develop your creative eye, build consistency in your practice, and create a diverse collection of memories.

---
Capturing life's beauty, one challenge at a time
Happy shooting from the Quivio team!
        """
        
        return await self.send_email(
            to_emails=[email],
            subject=f"Today's Photography Challenge ({difficulty.title()}) - {username}",
            html_content=html_template,
            text_content=text_content
        )

# Create global instance
email_service = EmailService()