import pandas as pd
from services.dataset_loader import dataset_loader
from services.ml_recommender import similarity_rank, encode_text, safe_num


def _status(score):
    if score >= 0.80:
        return "Highly Recommended"
    if score >= 0.55:
        return "Recommended"
    return "Partially Eligible"


def college_eligibility(data):
    df = dataset_loader.get("colleges")
    if df.empty:
        return []

    feature_rows = []
    for _, row in df.iterrows():
        feature_rows.append([
            encode_text(row.get("courses_offered", "")),
            encode_text(row.get("entrance_exam_required", "")),
            encode_text(row.get("mode_of_study", "")),
            encode_text(row.get("hostel_facilities", "")),
            safe_num(row.get("min_percentage_required", 0)),
        ])

    user_vector = [
        encode_text(data.get("course_offered", "")),
        encode_text(data.get("entrance_exam_required", "")),
        encode_text(data.get("mode_of_study", "")),
        encode_text(data.get("hostel_required", "")),
        safe_num(data.get("percentage", 0)),
    ]

    ranked = similarity_rank(df, feature_rows, user_vector, top_n=12)

    results = []
    for _, row in ranked.iterrows():
        results.append({
            "college_name": row.get("college_name", row.get("college name", "")),
            "location": row.get("location", ""),
            "affiliated_university": row.get("affiliated_university", ""),
            "accreditation": row.get("accreditation", ""),
            "tuition_fees": row.get("tuition_fees", ""),
            "scholarships_available": row.get("scholarships_available", ""),
            "placement_assistance": row.get("placement_assistance", ""),
            "region": row.get("region", ""),
            "infrastructure": row.get("infrastructure", ""),
            "accredited_by": row.get("accredited_by", ""),
            "contact_number": row.get("contact_number", ""),
            "email_address": row.get("email_address", ""),
            "website_url": row.get("website_url", ""),
            "apply_link": row.get("apply_link", ""),
            "eligibility_status": _status(row.get("ml_score", 0)),
        })
    return results


def job_eligibility(data, user):
    df = dataset_loader.get("jobs_exams")
    if df.empty:
        return []

    filtered = df.copy()

    if "exam_name" in filtered.columns and data.get("exam_name"):
        filtered = filtered[
            filtered["exam_name"].astype(str).str.contains(
                str(data.get("exam_name", "")), case=False, na=False
            )
        ]

    if "min_age" in filtered.columns:
        filtered["min_age"] = pd.to_numeric(filtered["min_age"], errors="coerce").fillna(0)
        filtered = filtered[filtered["min_age"] <= float(user.age or 0)]

    if "max_age" in filtered.columns:
        filtered["max_age"] = pd.to_numeric(filtered["max_age"], errors="coerce").fillna(999)
        filtered = filtered[filtered["max_age"] >= float(user.age or 0)]

    if "candidate_category" in filtered.columns and user.category:
        filtered = filtered[
            filtered["candidate_category"].astype(str).str.contains(
                str(user.category), case=False, na=False
            )
        ]

    results = []
    for _, row in filtered.head(12).iterrows():
        results.append({
            "post_name": row.get("post_name", ""),
            "department": row.get("department", ""),
            "job_location": row.get("job_location", ""),
            "apply_link": row.get("apply_link", ""),
            "website_url": row.get("website_url", ""),
            "eligibility_status": "Recommended",
        })
    return results


def exam_eligibility(data):
    df = dataset_loader.get("jobs_exams")
    if df.empty:
        return []

    filtered = df.copy()

    if "percentage" in filtered.columns:
        filtered["percentage"] = pd.to_numeric(filtered["percentage"], errors="coerce").fillna(0)
        filtered = filtered[filtered["percentage"] <= float(data.get("percentage", 0))]

    if "education_required" in filtered.columns and data.get("education_required"):
        filtered = filtered[
            filtered["education_required"].astype(str).str.contains(
                str(data.get("education_required", "")), case=False, na=False
            )
        ]

    if "state" in filtered.columns and data.get("state"):
        state_value = str(data.get("state", ""))
        if state_value.lower() != "all india":
            filtered = filtered[
                filtered["state"].astype(str).str.contains(state_value, case=False, na=False)
            ]

    if "candidate_category" in filtered.columns and data.get("candidate_category"):
        filtered = filtered[
            filtered["candidate_category"].astype(str).str.contains(
                str(data.get("candidate_category", "")), case=False, na=False
            )
        ]

    results = []
    for _, row in filtered.head(12).iterrows():
        results.append({
            "exam_name": row.get("exam_name", ""),
            "exam_category": row.get("exam_category", ""),
            "exam_id": row.get("exam_id", ""),
            "age_relaxation": row.get("age_relaxation", ""),
            "apply_link": row.get("apply_link", ""),
            "website_url": row.get("website_url", ""),
            "eligibility_status": "Recommended",
        })
    return results


def internship_eligibility(data, user):

    df = dataset_loader.get("internships")

    if df.empty:
        return []

    results = []

    for _, row in df.head(12).iterrows():

        results.append({
            "sector": row.get("sector", ""),
            "location_city": row.get("location_city", ""),
            "duration": row.get("duration", ""),
            "stipend_per_month_inr": row.get("stipend_per_month_inr", ""),
            "mode": row.get("mode", ""),
            "apply_link": row.get("apply_link", ""),
            "website_url": row.get("website_url", ""),
            "eligibility_status": "Recommended"
        })

    return results

def scholarship_eligibility(data, user):
    df = dataset_loader.get("scholarships")
    if df.empty:
        return []

    filtered = df.copy()

    student_class = str(data.get("student_class", "")).strip()
    user_marks = float(data.get("min_marks_required", 0) or 0)
    user_income = float(user.income or 0)
    eligible_category = str(data.get("eligible_category", "")).strip()
    scholarship_type = str(data.get("scholarship_type", "")).strip()

    if "min_marks_required" in filtered.columns:
        filtered["min_marks_required"] = pd.to_numeric(
            filtered["min_marks_required"], errors="coerce"
        ).fillna(0)
        filtered = filtered[filtered["min_marks_required"] <= user_marks]

    if "income_limit" in filtered.columns:
        filtered["income_limit"] = pd.to_numeric(
            filtered["income_limit"], errors="coerce"
        ).fillna(999999999)
        filtered = filtered[filtered["income_limit"] >= user_income]

    if "eligible_category" in filtered.columns and eligible_category and eligible_category.lower() != "all":
        filtered = filtered[
            filtered["eligible_category"].astype(str).str.contains(
                eligible_category, case=False, na=False
            )
        ]

    if "scholarship_type" in filtered.columns and scholarship_type and scholarship_type.lower() != "all":
        filtered = filtered[
            filtered["scholarship_type"].astype(str).str.contains(
                scholarship_type, case=False, na=False
            )
        ]

    if student_class:
        if "min_class" in filtered.columns:
            max_class_series = (
                filtered["max_class"].astype(str)
                if "max_class" in filtered.columns
                else pd.Series([""] * len(filtered), index=filtered.index)
            )

            filtered = filtered[
                filtered["min_class"].astype(str).str.contains(student_class, case=False, na=False)
                | max_class_series.str.contains(student_class, case=False, na=False)
            ]

    results = []
    for _, row in filtered.head(12).iterrows():
        results.append({
            "scholarship_id": row.get("scholarship_id", ""),
            "scholarship_name": row.get("scholarship_name", ""),
            "scholarship_type": row.get("scholarship_type", ""),
            "annual_scholarship_amount": row.get("annual_scholarship_amount", ""),
            "application_deadline": row.get("application_deadline", ""),
            "monthly_stipend": row.get("monthly_stipend", ""),
            "hostel_allowance": row.get("hostel_allowance", ""),
            "apply_link": row.get("apply_link", ""),
            "website_url": row.get("website_url", ""),
            "eligibility_status": "Recommended",
        })
    return results


def scheme_eligibility(data, user=None):
    df = dataset_loader.get("schemes")
    if df.empty:
        return []

    original_df = df.copy()
    filtered = df.copy()

    user_age = float(data.get("max_age", 0) or 0)
    category = str(data.get("category", "")).strip().lower()
    gender = str(data.get("gender", "")).strip().lower()
    state = str(data.get("states", "")).strip().lower()

    if "max_age" in filtered.columns and user_age > 0:
        filtered["max_age"] = pd.to_numeric(filtered["max_age"], errors="coerce").fillna(999)
        filtered = filtered[filtered["max_age"] >= user_age]

    if "category" in filtered.columns and category and category != "all":
        filtered = filtered[
            filtered["category"].astype(str).str.lower().str.contains(category, na=False)
        ]

    if "gender" in filtered.columns and gender and gender != "all":
        filtered = filtered[
            filtered["gender"].astype(str).str.lower().str.contains(gender, na=False)
        ]

    if "states" in filtered.columns and state and state != "all india":
        filtered = filtered[
            filtered["states"].astype(str).str.lower().str.contains(state, na=False)
        ]

    # fallback 1: category + gender
    if filtered.empty:
        fallback = original_df.copy()

        if "category" in fallback.columns and category and category != "all":
            fallback = fallback[
                fallback["category"].astype(str).str.lower().str.contains(category, na=False)
            ]

        if "gender" in fallback.columns and gender and gender != "all":
            fallback = fallback[
                fallback["gender"].astype(str).str.lower().str.contains(gender, na=False)
            ]

        filtered = fallback

    # fallback 2: category only
    if filtered.empty:
        fallback = original_df.copy()

        if "category" in fallback.columns and category and category != "all":
            fallback = fallback[
                fallback["category"].astype(str).str.lower().str.contains(category, na=False)
            ]

        filtered = fallback

    # fallback 3: top rows
    if filtered.empty:
        filtered = original_df.head(12)

    results = []
    for _, row in filtered.head(12).iterrows():
        results.append({
            "scheme_id": row.get("scheme_id", ""),
            "scheme_name": row.get("scheme_name", ""),
            "ministry": row.get("ministry", ""),
            "benefits": row.get("benefits", ""),
            "apply_link": row.get("apply_link", ""),
            "website_url": row.get("website_url", ""),
            "eligibility_status": "Recommended"
        })

    return results
