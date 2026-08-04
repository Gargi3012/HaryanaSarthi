import os
import sys

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Base, engine
from seed_data import create_dummy_users
from services.dataset_loader import dataset_loader

def test_migration():
    print("[TEST] Ensuring database tables are created...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("[TEST] Seeding user profiles...")
        create_dummy_users(db)
        
        print("[TEST] Loading opportunity CSV files...")
        dataset_loader.load_all()
        
        print("[TEST] Migrating opportunity data to database...")
        dataset_loader.migrate_to_db(db)
        
        print("[TEST] Success! Database tables populated and user seeds processed successfully.")
    except Exception as e:
        print(f"[TEST ERROR] Migration test failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_migration()
