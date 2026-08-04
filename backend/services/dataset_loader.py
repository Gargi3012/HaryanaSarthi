import os
import pandas as pd
from sqlalchemy.orm import Session
from models import College, JobExam, Internship, Scholarship, Scheme

class DatasetLoader:
    def __init__(self):
        self.datasets = {}

    def load_all(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))

        possible_paths = {
            "colleges": [
                os.path.join(base_dir, "data", "cleaned", "Colleges_cleaned.csv"),
                os.path.join(base_dir, "data", "colleges_cleaned.csv"),
            ],
            "jobs_exams": [
                os.path.join(base_dir, "data", "cleaned", "Job&Exam_cleaned.csv"),
                os.path.join(base_dir, "data", "Job&Exam_cleaned.csv"),
            ],
            "internships": [
                # FIXED: removed the wrong Job&Exam path and kept only the correct internship file path
                os.path.join(base_dir, "data", "cleaned", "internships_cleaned.csv"),
            ],
            "scholarships": [
                os.path.join(base_dir, "data", "cleaned", "haryana_scholarships_cleaned.csv"),
            ],
            "schemes": [
                os.path.join(base_dir, "data", "cleaned", "schemes_cleaned.csv"),
                os.path.join(base_dir, "data", "schemes_cleaned.csv"),
            ],
        }

        for key, paths in possible_paths.items():
            loaded = False

            for path in paths:
                if os.path.exists(path):
                    try:
                        self.datasets[key] = pd.read_csv(path)
                        print(f"[DATASET LOADED] {key}: {path}")
                        print(f"[COLUMNS] {key}: {list(self.datasets[key].columns)}")
                        loaded = True
                        break
                    except Exception as e:
                        print(f"[DATASET LOAD ERROR] {key}: {path} -> {e}")

            if not loaded:
                self.datasets[key] = pd.DataFrame()
                print(f"[DATASET NOT FOUND] {key}")

    def get(self, name: str):
        return self.datasets.get(name, pd.DataFrame())

    def _safe_float(self, val, default=0.0):
        try:
            if pd.isna(val):
                return default
            return float(val)
        except Exception:
            return default

    def migrate_to_db(self, db: Session):
        print("[DATABASE MIGRATION] Checking CSV to DB migration status...")

        # 1. Colleges
        if db.query(College).count() == 0 and "colleges" in self.datasets and not self.datasets["colleges"].empty:
            print("[DATABASE MIGRATION] Migrating Colleges...")
            colleges_to_insert = []
            for _, row in self.datasets["colleges"].iterrows():
                colleges_to_insert.append(College(
                    college_name=str(row.get("college_name", row.get("college name", ""))).strip(),
                    location=str(row.get("location", "")) if not pd.isna(row.get("location")) else None,
                    affiliated_university=str(row.get("affiliated_university", "")) if not pd.isna(row.get("affiliated_university")) else None,
                    accreditation=str(row.get("accreditation", "")) if not pd.isna(row.get("accreditation")) else None,
                    tuition_fees=str(row.get("tuition_fees", "")) if not pd.isna(row.get("tuition_fees")) else None,
                    scholarships_available=str(row.get("scholarships_available", "")) if not pd.isna(row.get("scholarships_available")) else None,
                    placement_assistance=str(row.get("placement_assistance", "")) if not pd.isna(row.get("placement_assistance")) else None,
                    region=str(row.get("region", "")) if not pd.isna(row.get("region")) else None,
                    infrastructure=str(row.get("infrastructure", "")) if not pd.isna(row.get("infrastructure")) else None,
                    accredited_by=str(row.get("accredited_by", "")) if not pd.isna(row.get("accredited_by")) else None,
                    contact_number=str(row.get("contact_number", "")) if not pd.isna(row.get("contact_number")) else None,
                    email_address=str(row.get("email_address", "")) if not pd.isna(row.get("email_address")) else None,
                    website_url=str(row.get("website_url", "")) if not pd.isna(row.get("website_url")) else None,
                    apply_link=str(row.get("apply_link", "")) if not pd.isna(row.get("apply_link")) else None,
                    min_percentage_required=self._safe_float(row.get("min_percentage_required")),
                    courses_offered=str(row.get("courses_offered", "")) if not pd.isna(row.get("courses_offered")) else None,
                    entrance_exam_required=str(row.get("entrance_exam_required", "")) if not pd.isna(row.get("entrance_exam_required")) else None,
                    mode_of_study=str(row.get("mode_of_study", "")) if not pd.isna(row.get("mode_of_study")) else None,
                    hostel_facilities=str(row.get("hostel_facilities", "")) if not pd.isna(row.get("hostel_facilities")) else None,
                ))
            db.bulk_save_objects(colleges_to_insert)
            db.commit()
            print(f"[DATABASE MIGRATION] Successfully migrated {len(colleges_to_insert)} Colleges.")

        # 2. Jobs / Exams (50,000 rows, run under transaction)
        if db.query(JobExam).count() == 0 and "jobs_exams" in self.datasets and not self.datasets["jobs_exams"].empty:
            print("[DATABASE MIGRATION] Migrating Jobs & Exams (this might take a second)...")
            records = []
            for _, row in self.datasets["jobs_exams"].iterrows():
                records.append(JobExam(
                    exam_name=str(row.get("exam_name", "")) if not pd.isna(row.get("exam_name")) else None,
                    post_name=str(row.get("post_name", "")) if not pd.isna(row.get("post_name")) else None,
                    department=str(row.get("department", "")) if not pd.isna(row.get("department")) else None,
                    job_location=str(row.get("job_location", "")) if not pd.isna(row.get("job_location")) else None,
                    min_age=self._safe_float(row.get("min_age"), 0.0),
                    max_age=self._safe_float(row.get("max_age"), 999.0),
                    candidate_category=str(row.get("candidate_category", "")) if not pd.isna(row.get("candidate_category")) else None,
                    education_required=str(row.get("education_required", "")) if not pd.isna(row.get("education_required")) else None,
                    percentage=self._safe_float(row.get("percentage"), 0.0),
                    state=str(row.get("state", "")) if not pd.isna(row.get("state")) else None,
                    exam_category=str(row.get("exam_category", "")) if not pd.isna(row.get("exam_category")) else None,
                    exam_id=str(row.get("exam_id", "")) if not pd.isna(row.get("exam_id")) else None,
                    age_relaxation=str(row.get("age_relaxation", "")) if not pd.isna(row.get("age_relaxation")) else None,
                    apply_link=str(row.get("apply_link", "")) if not pd.isna(row.get("apply_link")) else None,
                    website_url=str(row.get("website_url", "")) if not pd.isna(row.get("website_url")) else None,
                ))
            db.bulk_save_objects(records)
            db.commit()
            print(f"[DATABASE MIGRATION] Successfully migrated {len(records)} Jobs & Exams.")

        # 3. Internships
        if db.query(Internship).count() == 0 and "internships" in self.datasets and not self.datasets["internships"].empty:
            print("[DATABASE MIGRATION] Migrating Internships...")
            records = []
            for _, row in self.datasets["internships"].iterrows():
                records.append(Internship(
                    sector=str(row.get("sector", "")) if not pd.isna(row.get("sector")) else None,
                    location_city=str(row.get("location_city", "")) if not pd.isna(row.get("location_city")) else None,
                    duration=str(row.get("duration", "")) if not pd.isna(row.get("duration")) else None,
                    stipend_per_month_inr=str(row.get("stipend_per_month_inr", "")) if not pd.isna(row.get("stipend_per_month_inr")) else None,
                    mode=str(row.get("mode", "")) if not pd.isna(row.get("mode")) else None,
                    apply_link=str(row.get("apply_link", "")) if not pd.isna(row.get("apply_link")) else None,
                    website_url=str(row.get("website_url", "")) if not pd.isna(row.get("website_url")) else None,
                ))
            db.bulk_save_objects(records)
            db.commit()
            print(f"[DATABASE MIGRATION] Successfully migrated {len(records)} Internships.")

        # 4. Scholarships
        if db.query(Scholarship).count() == 0 and "scholarships" in self.datasets and not self.datasets["scholarships"].empty:
            print("[DATABASE MIGRATION] Migrating Scholarships...")
            records = []
            for _, row in self.datasets["scholarships"].iterrows():
                records.append(Scholarship(
                    scholarship_id=str(row.get("scholarship_id", "")) if not pd.isna(row.get("scholarship_id")) else None,
                    scholarship_name=str(row.get("scholarship_name", "")).strip(),
                    scholarship_type=str(row.get("scholarship_type", "")) if not pd.isna(row.get("scholarship_type")) else None,
                    annual_scholarship_amount=str(row.get("annual_scholarship_amount", "")) if not pd.isna(row.get("annual_scholarship_amount")) else None,
                    application_deadline=str(row.get("application_deadline", "")) if not pd.isna(row.get("application_deadline")) else None,
                    monthly_stipend=str(row.get("monthly_stipend", "")) if not pd.isna(row.get("monthly_stipend")) else None,
                    hostel_allowance=str(row.get("hostel_allowance", "")) if not pd.isna(row.get("hostel_allowance")) else None,
                    min_marks_required=self._safe_float(row.get("min_marks_required"), 0.0),
                    income_limit=self._safe_float(row.get("income_limit"), 999999999.0),
                    eligible_category=str(row.get("eligible_category", "")) if not pd.isna(row.get("eligible_category")) else None,
                    min_class=str(row.get("min_class", "")) if not pd.isna(row.get("min_class")) else None,
                    max_class=str(row.get("max_class", "")) if not pd.isna(row.get("max_class")) else None,
                    apply_link=str(row.get("apply_link", "")) if not pd.isna(row.get("apply_link")) else None,
                    website_url=str(row.get("website_url", "")) if not pd.isna(row.get("website_url")) else None,
                ))
            db.bulk_save_objects(records)
            db.commit()
            print(f"[DATABASE MIGRATION] Successfully migrated {len(records)} Scholarships.")

        # 5. Schemes
        if db.query(Scheme).count() == 0 and "schemes" in self.datasets and not self.datasets["schemes"].empty:
            print("[DATABASE MIGRATION] Migrating Schemes...")
            records = []
            for _, row in self.datasets["schemes"].iterrows():
                records.append(Scheme(
                    scheme_id=str(row.get("scheme_id", "")) if not pd.isna(row.get("scheme_id")) else None,
                    scheme_name=str(row.get("scheme_name", "")).strip(),
                    ministry=str(row.get("ministry", "")) if not pd.isna(row.get("ministry")) else None,
                    benefits=str(row.get("benefits", "")) if not pd.isna(row.get("benefits")) else None,
                    max_age=self._safe_float(row.get("max_age"), 999.0),
                    category=str(row.get("category", "")) if not pd.isna(row.get("category")) else None,
                    gender=str(row.get("gender", "")) if not pd.isna(row.get("gender")) else None,
                    states=str(row.get("states", "")) if not pd.isna(row.get("states")) else None,
                    apply_link=str(row.get("apply_link", "")) if not pd.isna(row.get("apply_link")) else None,
                    website_url=str(row.get("website_url", "")) if not pd.isna(row.get("website_url")) else None,
                ))
            db.bulk_save_objects(records)
            db.commit()
            print(f"[DATABASE MIGRATION] Successfully migrated {len(records)} Schemes.")

        print("[DATABASE MIGRATION] Migration checks completed.")

dataset_loader = DatasetLoader()