from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import (
    CollegeEligibilityRequest,
    JobEligibilityRequest,
    ExamEligibilityRequest,
    InternshipEligibilityRequest,
    ScholarshipEligibilityRequest,
    SchemeEligibilityRequest,
)
from services.eligibility_service import (
    college_eligibility,
    job_eligibility,
    exam_eligibility,
    internship_eligibility,
    scholarship_eligibility,
    scheme_eligibility,
)

router = APIRouter(prefix="/eligibility", tags=["eligibility"])


def _get_user(db: Session, user_id: str):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/colleges")
def colleges(payload: CollegeEligibilityRequest, db: Session = Depends(get_db)):
    _get_user(db, payload.user_id)
    return {
        "message": "College eligibility checked successfully",
        "results": college_eligibility(payload.dict())
    }


@router.post("/jobs")
def jobs(payload: JobEligibilityRequest, db: Session = Depends(get_db)):
    user = _get_user(db, payload.user_id)
    return {
        "message": "Job eligibility checked successfully",
        "results": job_eligibility(payload.dict(), user)
    }


@router.post("/exams")
def exams(payload: ExamEligibilityRequest, db: Session = Depends(get_db)):
    _get_user(db, payload.user_id)
    return {
        "message": "Exam eligibility checked successfully",
        "results": exam_eligibility(payload.dict())
    }


@router.post("/internships")
def internships(payload: InternshipEligibilityRequest, db: Session = Depends(get_db)):
    user = _get_user(db, payload.user_id)
    return {
        "message": "Internship eligibility checked successfully",
        "results": internship_eligibility(payload.dict(), user)
    }


@router.post("/scholarships")
def scholarships(payload: ScholarshipEligibilityRequest, db: Session = Depends(get_db)):
    user = _get_user(db, payload.user_id)
    return {
        "message": "Scholarship eligibility checked successfully",
        "results": scholarship_eligibility(payload.dict(), user)
    }


@router.post("/schemes")
def schemes(payload: SchemeEligibilityRequest, db: Session = Depends(get_db)):
    user = _get_user(db, payload.user_id)
    return {
        "message": "Scheme eligibility checked successfully",
        "results": scheme_eligibility(payload.dict(), user)
    }