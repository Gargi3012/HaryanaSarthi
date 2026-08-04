from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
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


class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    college_name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=True)
    affiliated_university = Column(String, nullable=True)
    accreditation = Column(String, nullable=True)
    tuition_fees = Column(String, nullable=True)
    scholarships_available = Column(String, nullable=True)
    placement_assistance = Column(String, nullable=True)
    region = Column(String, nullable=True)
    infrastructure = Column(String, nullable=True)
    accredited_by = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    email_address = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    apply_link = Column(String, nullable=True)
    min_percentage_required = Column(Float, default=0.0)
    courses_offered = Column(String, nullable=True)
    entrance_exam_required = Column(String, nullable=True)
    mode_of_study = Column(String, nullable=True)
    hostel_facilities = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)


class JobExam(Base):
    __tablename__ = "jobs_exams"

    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String, index=True, nullable=True)
    post_name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    job_location = Column(String, nullable=True)
    min_age = Column(Float, default=0.0)
    max_age = Column(Float, default=999.0)
    candidate_category = Column(String, nullable=True)
    education_required = Column(String, nullable=True)
    percentage = Column(Float, default=0.0)
    state = Column(String, nullable=True)
    exam_category = Column(String, nullable=True)
    exam_id = Column(String, nullable=True)
    age_relaxation = Column(String, nullable=True)
    apply_link = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)


class Internship(Base):
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True, index=True)
    sector = Column(String, index=True, nullable=True)
    location_city = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    stipend_per_month_inr = Column(String, nullable=True)
    mode = Column(String, nullable=True)
    apply_link = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)


class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, index=True)
    scholarship_id = Column(String, index=True, nullable=True)
    scholarship_name = Column(String, index=True, nullable=False)
    scholarship_type = Column(String, nullable=True)
    annual_scholarship_amount = Column(String, nullable=True)
    application_deadline = Column(String, nullable=True)
    monthly_stipend = Column(String, nullable=True)
    hostel_allowance = Column(String, nullable=True)
    min_marks_required = Column(Float, default=0.0)
    income_limit = Column(Float, default=999999999.0)
    eligible_category = Column(String, nullable=True)
    min_class = Column(String, nullable=True)
    max_class = Column(String, nullable=True)
    apply_link = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(String, index=True, nullable=True)
    scheme_name = Column(String, index=True, nullable=False)
    ministry = Column(String, nullable=True)
    benefits = Column(String, nullable=True)
    max_age = Column(Float, default=999.0)
    category = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    states = Column(String, nullable=True)
    apply_link = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)