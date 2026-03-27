from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    category = Column(String, nullable=True)
    income = Column(Float, nullable=True)
    occupation = Column(String, nullable=True)
    caste = Column(String, nullable=True)
    divyang = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    state = Column(String, nullable=True)
    current_class = Column(String, nullable=True)
    education = Column(String, nullable=True)
    percentage = Column(Float, nullable=True)
    password_hash = Column(String, nullable=False)


class OnboardingData(Base):
    __tablename__ = "onboarding_data"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)

    user_type = Column(String, nullable=True)
    looking_for = Column(String, nullable=True)
    category = Column(String, nullable=True)
    location_preference = Column(String, nullable=True)

    step1_completed = Column(Boolean, default=False)
    step2_completed = Column(Boolean, default=False)
    step3_completed = Column(Boolean, default=False)
    step4_completed = Column(Boolean, default=False)

    step1_skipped = Column(Boolean, default=False)
    step2_skipped = Column(Boolean, default=False)
    step3_skipped = Column(Boolean, default=False)
    step4_skipped = Column(Boolean, default=False)