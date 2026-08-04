from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from database import get_async_db
from models import College, JobExam, Scholarship, Internship, Scheme

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_async_db)):
    # Run async count queries for each opportunity table
    colleges_count = (await db.execute(select(func.count(College.id)))).scalar_one() or 0
    jobs_exams_count = (await db.execute(select(func.count(JobExam.id)))).scalar_one() or 0
    scholarships_count = (await db.execute(select(func.count(Scholarship.id)))).scalar_one() or 0
    internships_count = (await db.execute(select(func.count(Internship.id)))).scalar_one() or 0
    schemes_count = (await db.execute(select(func.count(Scheme.id)))).scalar_one() or 0

    return {
        "colleges": colleges_count,
        "jobs_exams": jobs_exams_count,
        "scholarships": scholarships_count,
        "internships": internships_count,
        "schemes": schemes_count,
    }