#test_email.py
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import email_service

async def test_email():
    """Test email service"""
    print("Testing email service...")
    
    if not email_service.enabled:
        print("❌ Email service is not enabled. Check your .env configuration.")
        return
    
    # Test sending a simple email
    success = await email_service.send_email(
        to_emails=["quivio.dev@gmail.com"],  # Send to yourself for testing
        subject="🎉 Quivio Email Test",
        html_content="""
        <h2>Email Service Working!</h2>
        <p>Your Quivio email service is configured correctly.</p>
        <p>Ready to implement password reset and capsule notifications!</p>
        """,
        text_content="Email Service Working! Your Quivio email service is configured correctly."
    )
    
    if success:
        print("✅ Email sent successfully! Check quivio.dev@gmail.com")
    else:
        print("❌ Failed to send email. Check your email configuration.")

if __name__ == "__main__":
    asyncio.run(test_email())