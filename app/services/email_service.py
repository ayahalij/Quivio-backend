# app/services/email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import List, Optional
from jinja2 import Template
import requests
from app.core.config import settings
import logging

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

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email to one or more recipients"""
        if not self.enabled:
            logger.warning("Email service is disabled or not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.smtp_user}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Create secure connection and send
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_emails}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

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
        is_personal: bool = True
    ) -> bool:
        """Send capsule opening notification email"""
        
        if is_personal:
            subject = f"🎉 Your Memory Capsule '{capsule_title}' Has Opened!"
            greeting = f"Hello {sender_name}!"
            intro = "Your memory capsule has reached its opening date and is now available to view!"
        else:
            subject = f"🎁 {sender_name} Sent You a Memory Capsule!"
            greeting = "Hello!"
            intro = f"{sender_name} has shared a special memory capsule with you through Quivio!"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ subject }}</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .capsule-content { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50; }
                .button { display: inline-block; background: #4caf50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                .footer { text-align: center; margin-top: 30px; color: #666; font-size: 14px; }
                .meta { color: #666; font-size: 14px; margin-top: 10px; }
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
                    
                    {% if is_personal %}
                    <p>You can view this capsule and any attached media in your Quivio timeline:</p>
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
            frontend_url=settings.FRONTEND_URL
        )
        
        text_content = f"""
{greeting}

{intro}

Memory Capsule: {capsule_title}

Message:
{capsule_message}

Created: {created_date}
{'From: ' + sender_name if not is_personal else ''}

{'View in Quivio: ' + settings.FRONTEND_URL + '/timeline' if is_personal else 'Explore Quivio: ' + settings.FRONTEND_URL}
        """
        
        return await self.send_email(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            text_content=text_content.strip()
        )

# Create global instance
email_service = EmailService()