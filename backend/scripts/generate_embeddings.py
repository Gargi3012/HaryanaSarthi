import os
import sys

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import College, Scholarship, Scheme, Internship
from services.gemini_service import get_embedding

def build_college_text(item) -> str:
    return f"College: {item.college_name}. Location: {item.location}. University: {item.affiliated_university}. Courses: {item.courses_offered}. Eligibility: min percentage required {item.min_percentage_required}%. Study mode: {item.mode_of_study}. Hostel: {item.hostel_facilities}."

def build_scholarship_text(item) -> str:
    return f"Scholarship: {item.scholarship_name}. Type: {item.scholarship_type}. Amount: {item.annual_scholarship_amount}. Eligibility: category {item.eligible_category}, min marks required {item.min_marks_required}%, income limit {item.income_limit} INR. Class: {item.min_class} to {item.max_class}."

def build_scheme_text(item) -> str:
    return f"Scheme: {item.scheme_name}. Ministry: {item.ministry}. Benefits: {item.benefits}. Eligibility: category {item.category}, gender {item.gender}, max age {item.max_age}, states {item.states}."

def build_internship_text(item) -> str:
    return f"Internship Sector: {item.sector}. City: {item.location_city}. Duration: {item.duration}. Stipend: {item.stipend_per_month_inr} INR. Mode: {item.mode}."

def backfill_embeddings():
    db = SessionLocal()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[BACKFILL ERROR] GEMINI_API_KEY environment variable is not configured. Cannot generate embeddings.")
        return

    targets = [
        (College, build_college_text, "Colleges"),
        (Scholarship, build_scholarship_text, "Scholarships"),
        (Scheme, build_scheme_text, "Schemes"),
        (Internship, build_internship_text, "Internships"),
    ]

    try:
        for model_class, text_builder, name in targets:
            # Query all items that don't have embeddings populated yet
            items = db.query(model_class).filter(model_class.embedding == None).all()
            if not items:
                print(f"[BACKFILL] All {name} already have vector embeddings.")
                continue

            print(f"[BACKFILL] Found {len(items)} {name} without embeddings. Backfilling now...")
            count = 0
            for item in items:
                text_blob = text_builder(item)
                vector = get_embedding(text_blob)
                if vector:
                    item.embedding = vector
                    count += 1
                    # Commit in batches of 20
                    if count % 20 == 0:
                        db.commit()
                        print(f"[BACKFILL] Processed {count}/{len(items)} {name}...")
            db.commit()
            print(f"[BACKFILL] Completed backfill for {count} {name}.")
    except Exception as e:
        print(f"[BACKFILL ERROR] An unexpected error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill_embeddings()
