from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from models import College, JobExam, Internship, Scholarship, Scheme, User
from services.gemini_service import get_embedding_async
from services.ml_recommender import search_opportunities_vector

def _status(score):
    if score >= 0.70:
        return "Highly Recommended"
    if score >= 0.50:
        return "Recommended"
    return "Partially Eligible"

async def college_eligibility(db: AsyncSession, data: dict) -> list:
    # Build query text representation for vector search
    user_text = f"Course: {data.get('course_offered', '')}. Entrance Exam: {data.get('entrance_exam_required', '')}. Study Mode: {data.get('mode_of_study', '')}. Hostel: {data.get('hostel_required', '')}. Percentage: {data.get('percentage', 0)}%."
    
    # Fetch dense multilingual embedding vector
    user_vector = await get_embedding_async(user_text)
    
    # Perform vector similarity search on Colleges table
    colleges = await search_opportunities_vector(db, College, user_vector, limit=12)
    
    results = []
    for c in colleges:
        results.append({
            "college_name": c.college_name,
            "location": c.location or "",
            "affiliated_university": c.affiliated_university or "",
            "accreditation": c.accreditation or "",
            "tuition_fees": c.tuition_fees or "",
            "scholarships_available": c.scholarships_available or "",
            "placement_assistance": c.placement_assistance or "",
            "region": c.region or "",
            "infrastructure": c.infrastructure or "",
            "accredited_by": c.accredited_by or "",
            "contact_number": c.contact_number or "",
            "email_address": c.email_address or "",
            "website_url": c.website_url or "",
            "apply_link": c.apply_link or "",
            "eligibility_status": _status(c.ml_score),
        })
    return results

async def job_eligibility(db: AsyncSession, data: dict, user: User) -> list:
    # SQL based strict credentials filtering for jobs
    filters = []
    
    if data.get("exam_name"):
        filters.append(JobExam.exam_name.ilike(f"%{data.get('exam_name')}%"))
        
    user_age = float(user.age or 0)
    filters.append(JobExam.min_age <= user_age)
    filters.append(JobExam.max_age >= user_age)
    
    if user.category:
        filters.append(JobExam.candidate_category.ilike(f"%{user.category}%"))
        
    query = select(JobExam).where(and_(*filters)).limit(12)
    jobs = (await db.execute(query)).scalars().all()
    
    results = []
    for j in jobs:
        results.append({
            "post_name": j.post_name or j.exam_name or "",
            "department": j.department or "",
            "job_location": j.job_location or "",
            "apply_link": j.apply_link or "",
            "website_url": j.website_url or "",
            "eligibility_status": "Recommended",
        })
    return results

async def exam_eligibility(db: AsyncSession, data: dict) -> list:
    # Strict validation queries
    filters = []
    
    user_marks = float(data.get("percentage") or 0.0)
    filters.append(JobExam.percentage <= user_marks)
    
    if data.get("education_required"):
        filters.append(JobExam.education_required.ilike(f"%{data.get('education_required')}%"))
        
    if data.get("state") and data.get("state").lower() != "all india":
        filters.append(JobExam.state.ilike(f"%{data.get('state')}%"))
        
    if data.get("candidate_category") and data.get("candidate_category").lower() != "all":
        filters.append(JobExam.candidate_category.ilike(f"%{data.get('candidate_category')}%"))
        
    query = select(JobExam).where(and_(*filters)).limit(12)
    exams = (await db.execute(query)).scalars().all()
    
    results = []
    for e in exams:
        results.append({
            "exam_name": e.exam_name or "",
            "exam_category": e.exam_category or "",
            "exam_id": e.exam_id or "",
            "age_relaxation": e.age_relaxation or "",
            "apply_link": e.apply_link or "",
            "website_url": e.website_url or "",
            "eligibility_status": "Recommended",
        })
    return results

async def internship_eligibility(db: AsyncSession, data: dict, user: User) -> list:
    # Multilingual embedding verification for internships
    user_text = f"Sector: {data.get('preferred_sector', '')}. Mode: {data.get('internship_mode', '')}. Duration: {data.get('preferred_duration', 0)} months. Marks: {data.get('percentage', 0)}%."
    user_vector = await get_embedding_async(user_text)
    
    internships = await search_opportunities_vector(db, Internship, user_vector, limit=12)
    
    results = []
    for i in internships:
        results.append({
            "sector": i.sector or "",
            "location_city": i.location_city or "",
            "duration": i.duration or "",
            "stipend_per_month_inr": i.stipend_per_month_inr or "",
            "mode": i.mode or "",
            "apply_link": i.apply_link or "",
            "website_url": i.website_url or "",
            "eligibility_status": _status(i.ml_score),
        })
    return results

async def scholarship_eligibility(db: AsyncSession, data: dict, user: User) -> list:
    # Hybrid search: strict filtering first, then vector similarity ranking
    filters = []
    
    student_class = str(data.get("student_class", "")).strip()
    user_marks = float(data.get("min_marks_required") or 0.0)
    user_income = float(user.income or 0.0)
    eligible_category = str(data.get("eligible_category", "")).strip()
    scholarship_type = str(data.get("scholarship_type", "")).strip()
    
    filters.append(Scholarship.min_marks_required <= user_marks)
    filters.append(Scholarship.income_limit >= user_income)
    
    if eligible_category and eligible_category.lower() != "all":
        filters.append(Scholarship.eligible_category.ilike(f"%{eligible_category}%"))
        
    if scholarship_type and scholarship_type.lower() != "all":
        filters.append(Scholarship.scholarship_type.ilike(f"%{scholarship_type}%"))
        
    if student_class:
        filters.append(or_(
            Scholarship.min_class.ilike(f"%{student_class}%"),
            Scholarship.max_class.ilike(f"%{student_class}%")
        ))
        
    user_text = f"Class: {student_class}. Marks: {user_marks}%. Income limit: {user_income} INR. Scholarship type: {scholarship_type}. Category: {eligible_category}."
    user_vector = await get_embedding_async(user_text)
    
    scholarships = await search_opportunities_vector(db, Scholarship, user_vector, limit=12, filters=filters)
    
    results = []
    for s in scholarships:
        results.append({
            "scholarship_id": s.scholarship_id or "",
            "scholarship_name": s.scholarship_name,
            "scholarship_type": s.scholarship_type or "",
            "annual_scholarship_amount": s.annual_scholarship_amount or "",
            "application_deadline": s.application_deadline or "",
            "monthly_stipend": s.monthly_stipend or "",
            "hostel_allowance": s.hostel_allowance or "",
            "apply_link": s.apply_link or "",
            "website_url": s.website_url or "",
            "eligibility_status": _status(s.ml_score),
        })
    return results

async def scheme_eligibility(db: AsyncSession, data: dict, user: User = None) -> list:
    # Hybrid search for government schemes
    filters = []
    
    user_age = float(data.get("max_age") or 0.0)
    category = str(data.get("category", "")).strip()
    gender = str(data.get("gender", "")).strip()
    state = str(data.get("states", "")).strip()
    
    if user_age > 0:
        filters.append(Scheme.max_age >= user_age)
        
    if category and category.lower() != "all":
        filters.append(Scheme.category.ilike(f"%{category}%"))
        
    if gender and gender.lower() != "all":
        filters.append(Scheme.gender.ilike(f"%{gender}%"))
        
    if state and state.lower() != "all india":
        filters.append(Scheme.states.ilike(f"%{state}%"))
        
    user_text = f"Scheme for Category: {category}. Gender: {gender}. Age: {user_age}. State: {state}."
    user_vector = await get_embedding_async(user_text)
    
    schemes = await search_opportunities_vector(db, Scheme, user_vector, limit=12, filters=filters)
    
    results = []
    for s in schemes:
        results.append({
            "scheme_id": s.scheme_id or "",
            "scheme_name": s.scheme_name,
            "ministry": s.ministry or "",
            "benefits": s.benefits or "",
            "apply_link": s.apply_link or "",
            "website_url": s.website_url or "",
            "eligibility_status": _status(s.ml_score),
        })
    return results
