import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models.user import User
from app.models.mood import Mood
from app.models.diary import DiaryEntry
from app.models.photo import Photo
from app.models.challenge import DailyChallenge, UserChallenge
from app.models.capsule import Capsule, CapsuleMedia
from app.models.password_reset import PasswordResetToken

def migrate_database():
    """Create new tables in the database"""
    print("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database migration completed successfully!")
        print("📝 New table created: password_reset_tokens")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_database()