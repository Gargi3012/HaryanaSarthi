from pydantic import BaseModel
from typing import Optional, Any


class LoginRequest(BaseModel):
    user_id: str
    password: str


class SaveStepRequest(BaseModel):
    step_number: int
    user_type: Optional[Any] = None
    looking_for: Optional[Any] = None
    category: Optional[Any] = None
    location_preference: Optional[Any] = None
    is_skipped: bool = False


class CollegeEligibilityRequest(BaseModel):
    user_id: str
    course_offered: str
    entrance_exam_required: str
    percentage: float
    mode_of_study: str
    hostel_required: str


class JobEligibilityRequest(BaseModel):
    user_id: str
    exam_name: str
    percentage: float


class ExamEligibilityRequest(BaseModel):
    user_id: str
    percentage: float
    education_required: str
    state: str
    candidate_category: str

class InternshipEligibilityRequest(BaseModel):
    user_id: str
    preferred_sector: str
    internship_mode: str
    preferred_duration: int
    percentage: float


class ScholarshipEligibilityRequest(BaseModel):
    user_id: str
    student_class: str
    min_marks_required: float
    eligible_category: str
    scholarship_type: str


class SchemeEligibilityRequest(BaseModel):
    user_id: str
    max_age: int
    category: str
    gender: str
    states: str


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    page: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    mode: str

class DocumentAnalysisRequest(BaseModel):
    opportunity_name: str
    file_name: str
    mime_type: str
    file_data: str
    user_id: Optional[str] = None