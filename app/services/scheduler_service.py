import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.capsule import Capsule
from app.api.endpoints.capsules import send_emails_background

async def check_and_open_capsules():
    """Check for capsules that should be opened and send emails"""
    db = next(get_db())
    try:
        current_time = datetime.now(timezone.utc)
        
        # Find capsules that should be opened but aren't yet
        ready_capsules = db.query(Capsule).filter(
            Capsule.is_opened == False,
            Capsule.open_date <= current_time
        ).all()
        
        for capsule in ready_capsules:
            # Mark as opened
            capsule.is_opened = True
            capsule.opened_at = current_time
            
            # Send emails
            send_emails_background(capsule.id)
            
        db.commit()
        print(f"Checked capsules: {len(ready_capsules)} opened automatically")
        
    except Exception as e:
        print(f"Error in capsule scheduler: {e}")
    finally:
        db.close()

# Run this every minute
async def start_capsule_scheduler():
    while True:
        await check_and_open_capsules()
        await asyncio.sleep(60)  # Check every minute