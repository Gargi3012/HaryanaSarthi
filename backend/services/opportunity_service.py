from services.dataset_loader import dataset_loader


def _safe_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def _top_records(df, count=4):
    if df is None or df.empty:
        return []
    # Fill NaN with empty string to prevent invalid JSON 'NaN' errors in browser
    return df.head(count).fillna("").to_dict(orient="records")


def get_recommended_opportunities(onboarding_data: dict):
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

    colleges_df = dataset_loader.get("colleges")
    jobs_exams_df = dataset_loader.get("jobs_exams")
    internships_df = dataset_loader.get("internships")
    scholarships_df = dataset_loader.get("scholarships")
    schemes_df = dataset_loader.get("schemes")

    if "college" in looking_for or "education" in looking_for or user_type == "student":
        results["colleges"] = _top_records(colleges_df, 4)

    if "scholarship" in looking_for or user_type == "student":
        results["scholarships"] = _top_records(scholarships_df, 4)

    if "job" in looking_for or user_type == "job seeker":
        results["jobs"] = _top_records(jobs_exams_df, 4)

    if "exam" in looking_for or user_type == "job seeker":
        results["exams"] = _top_records(jobs_exams_df, 4)

    if "internship" in looking_for or user_type == "student":
        results["internships"] = _top_records(internships_df, 4)

    if "scheme" in looking_for or user_type in ["farmer", "women beneficiary", "general citizen", "msme / business owner"]:
        if user_type == "general citizen" and any(k in looking_for for k in ["healthcare", "agriculture", "women_child", "transport", "housing"]):
            keywords = []
            if "healthcare" in looking_for: keywords.extend(["health"])
            if "agriculture" in looking_for: keywords.extend(["farmer", "agriculture"])
            if "women_child" in looking_for: keywords.extend(["women", "child", "girl"])
            if "transport" in looking_for: keywords.extend(["transport", "travel", "bus"])
            if "housing" in looking_for: keywords.extend(["housing", "awas"])
            
            mask = schemes_df.apply(lambda row: any(kw in str(row.values).lower() for kw in keywords), axis=1)
            results["schemes"] = _top_records(schemes_df[mask], 4)
        else:
            results["schemes"] = _top_records(schemes_df, 4)

    # fallback so page never looks empty
    if not any(results.values()):
        results["colleges"] = _top_records(colleges_df, 4)
        results["scholarships"] = _top_records(scholarships_df, 4)
        results["jobs"] = _top_records(jobs_exams_df, 4)
        results["internships"] = _top_records(internships_df, 4)
        results["schemes"] = _top_records(schemes_df, 4)

    # optional simple location/category preference influence
    if location_preference:
        for key in ["colleges", "jobs", "schemes"]:
            items = results.get(key, [])
            boosted = []
            others = []

            for item in items:
                text_blob = " ".join(str(v) for v in item.values()).lower()
                if location_preference in text_blob:
                    boosted.append(item)
                else:
                    others.append(item)

            results[key] = boosted + others

    if category:
        for key in ["scholarships", "schemes"]:
            items = results.get(key, [])
            boosted = []
            others = []

            for item in items:
                text_blob = " ".join(str(v) for v in item.values()).lower()
                if category in text_blob or "all" in text_blob:
                    boosted.append(item)
                else:
                    others.append(item)

            results[key] = boosted + others

    return results