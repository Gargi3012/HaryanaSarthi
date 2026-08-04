from sqlalchemy.orm import Session
from models import User
from services.auth_service import hash_password


def create_dummy_users(db: Session):
    # Only seed if the user table is empty, preventing destructive wipes on startup
    if db.query(User).count() > 0:
        print("[DATABASE] Users already exist. Skipping seeding.")
        return

    print("[DATABASE] Seeding dummy users...")
    
    users = [
        User(
            user_id="user1",
            name="Gargi Sharma",
            age=20,
            category="General",
            income=250000,
            occupation="Student",
            caste="General",
            divyang="No",
            gender="Female",
            state="Haryana",
            current_class="Undergraduate",
            education="Graduate",
            percentage=78.0,
            password_hash=hash_password("gargi123"),
        ),
        User(
            user_id="user2",
            name="Dev Rohilla",
            age=22,
            category="OBC",
            income=300000,
            occupation="Job Seeker",
            caste="OBC",
            divyang="No",
            gender="Male",
            state="Haryana",
            current_class="12th Pass",
            education="12th Pass",
            percentage=72.0,
            password_hash=hash_password("gargi123"),
        ),
        User(
            user_id="user3",
            name="Aditi Khasa",
            age=24,
            category="SC",
            income=180000,
            occupation="Student",
            caste="SC",
            divyang="No",
            gender="Female",
            state="Haryana",
            current_class="Postgraduate",
            education="Post Graduate",
            percentage=84.0,
            password_hash=hash_password("gargi123"),
        ),
    ]

    db.add_all(users)
    db.commit()
    print("[DATABASE] Dummy users seeded successfully.")