# migrate_capsule_recipients.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models.capsule_recipient import CapsuleRecipient

def migrate_capsule_recipients():
    print("Creating capsule recipients table...")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Capsule recipients table created successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_capsule_recipients()