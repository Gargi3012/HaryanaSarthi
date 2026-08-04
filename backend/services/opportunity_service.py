from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import College, Scholarship, JobExam, Internship, Scheme
from typing import Dict, Any

def _safe_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()

async def get_recommended_opportunities(db: AsyncSession, onboarding_data: dict) -> Dict[str, Any]:
    user_type = _safe_text(onboarding_data.get("user_type"))
    looking_for = onboarding_data.get("looking_for", [])
    if not isinstance(looking_for, list):
        looking_for = [looking_for] if looking_for else []

    looking_for = [_safe_text(x) for x in looking_for]
    category = _safe_text(onboarding_data.get("category"))
    location_preference = _safe_text(onboarding_data.get("location_preference"))

    results = {
        "colleges": [],
        "scholarships": [],
        "jobs": [],
        "exams": [],
        "internships": [],
        "schemes": [],
    }

    limit = 4

    def to_dict_list(objects):
        res = []
        for obj in objects:
            d = {col.name: getattr(obj, col.name) for col in obj.__table__.columns if col.name != "embedding"}
            if hasattr(obj, "ml_score"):
                d["ml_score"] = obj.ml_score
            res.append(d)
        return res

    # 1. Colleges
    if "college" in looking_for or "education" in looking_for or user_type == "student":
        q = select(College)
        if location_preference:
            q = q.order_by(College.location.ilike(f"%{location_preference}%").desc())
        q = q.limit(limit)
        colleges = (await db.execute(q)).scalars().all()
        results["colleges"] = to_dict_list(colleges)

    # 2. Scholarships
    if "scholarship" in looking_for or user_type == "student":
        q = select(Scholarship)
        if category:
            q = q.order_by(Scholarship.eligible_category.ilike(f"%{category}%").desc())
        q = q.limit(limit)
        scholarships = (await db.execute(q)).scalars().all()
        results["scholarships"] = to_dict_list(scholarships)

    # 3. Jobs & Exams
    if "job" in looking_for or user_type == "job seeker":
        q = select(JobExam).where(JobExam.exam_category.ilike("%job%"))
        if location_preference:
            q = q.order_by(JobExam.job_location.ilike(f"%{location_preference}%").desc())
        q = q.limit(limit)
        jobs = (await db.execute(q)).scalars().all()
        results["jobs"] = to_dict_list(jobs)

    if "exam" in looking_for or user_type == "job seeker":
        q = select(JobExam).where(JobExam.exam_category.ilike("%exam%"))
        q = q.limit(limit)
        exams = (await db.execute(q)).scalars().all()
        results["exams"] = to_dict_list(exams)

    # 4. Internships
    if "internship" in looking_for or user_type == "student":
        q = select(Internship)
        if location_preference:
            q = q.order_by(Internship.location_city.ilike(f"%{location_preference}%").desc())
        q = q.limit(limit)
        internships = (await db.execute(q)).scalars().all()
        results["internships"] = to_dict_list(internships)

    # 5. Schemes
    if "scheme" in looking_for or user_type in ["farmer", "women beneficiary", "general citizen", "msme / business owner"]:
        q = select(Scheme)
        if category:
            q = q.order_by(Scheme.category.ilike(f"%{category}%").desc())
        q = q.limit(limit)
        schemes = (await db.execute(q)).scalars().all()
        results["schemes"] = to_dict_list(schemes)

    # Fallback matching
    if not any(results.values()):
        results["colleges"] = to_dict_list((await db.execute(select(College).limit(limit))).scalars().all())
        results["scholarships"] = to_dict_list((await db.execute(select(Scholarship).limit(limit))).scalars().all())
        results["jobs"] = to_dict_list((await db.execute(select(JobExam).where(JobExam.exam_category.ilike("%job%")).limit(limit))).scalars().all())
        results["internships"] = to_dict_list((await db.execute(select(Internship).limit(limit))).scalars().all())
        results["schemes"] = to_dict_list((await db.execute(select(Scheme).limit(limit))).scalars().all())

    return results