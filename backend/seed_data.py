from sqlalchemy.orm import Session
from models import User


def create_dummy_users(db: Session):
    db.query(User).delete()
    db.commit()

    users = [
        User(
            user_id="user_id1",
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
            percentage=78,
            password_hash="gargi123",
        ),
        User(
            user_id="user_id2",
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
            percentage=72,
            password_hash="gargi123",
        ),
        User(
            user_id="user_id3",
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
            percentage=84,
            password_hash="gargi123",
        ),
    ]

    db.add_all(users)
    db.commit()