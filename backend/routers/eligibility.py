from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_async_db
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


async def _get_user(db: AsyncSession, user_id: str):
    query = select(User).where(User.user_id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    return user


@router.post("/colleges")
async def colleges(payload: CollegeEligibilityRequest, db: AsyncSession = Depends(get_async_db)):
    await _get_user(db, payload.user_id)
    results = await college_eligibility(db, payload.dict())
    return {
        "message": "College eligibility checked successfully",
        "results": results
    }


@router.post("/jobs")
async def jobs(payload: JobEligibilityRequest, db: AsyncSession = Depends(get_async_db)):
    user = await _get_user(db, payload.user_id)
    results = await job_eligibility(db, payload.dict(), user)
    return {
        "message": "Job eligibility checked successfully",
        "results": results
    }


@router.post("/exams")
async def exams(payload: ExamEligibilityRequest, db: AsyncSession = Depends(get_async_db)):
    await _get_user(db, payload.user_id)
    results = await exam_eligibility(db, payload.dict())
    return {
        "message": "Exam eligibility checked successfully",
        "results": results
    }


@router.post("/internships")
async def internships(payload: InternshipEligibilityRequest, db: AsyncSession = Depends(get_async_db)):
    user = await _get_user(db, payload.user_id)
    results = await internship_eligibility(db, payload.dict(), user)
    return {
        "message": "Internship eligibility checked successfully",
        "results": results
    }


@router.post("/scholarships")
async def scholarships(payload: ScholarshipEligibilityRequest, db: AsyncSession = Depends(get_async_db)):
    user = await _get_user(db, payload.user_id)
    results = await scholarship_eligibility(db, payload.dict(), user)
    return {
        "message": "Scholarship eligibility checked successfully",
        "results": results
    }


@router.post("/schemes")
async def schemes(payload: SchemeEligibilityRequest, db: AsyncSession = Depends(get_async_db)):
    user = await _get_user(db, payload.user_id)
    results = await scheme_eligibility(db, payload.dict(), user)
    return {
        "message": "Scheme eligibility checked successfully",
        "results": results
    }