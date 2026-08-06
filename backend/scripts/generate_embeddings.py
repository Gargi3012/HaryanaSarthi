import os
import sys
from dotenv import load_dotenv

# Ensure backend directory is in the path and load environment variables
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database import SessionLocal, Base, engine
from models import College, Scholarship, Scheme, Internship
from services.llm_service import get_embedding
from services.dataset_loader import dataset_loader
from services.qdrant_service import qdrant_service

def build_college_text(item) -> str:
    return f"College: {item.college_name}. Location: {item.location}. University: {item.affiliated_university}. Courses: {item.courses_offered}. Eligibility: min percentage required {item.min_percentage_required}%. Study mode: {item.mode_of_study}. Hostel: {item.hostel_facilities}."

def build_scholarship_text(item) -> str:
    return f"Scholarship: {item.scholarship_name}. Type: {item.scholarship_type}. Amount: {item.annual_scholarship_amount}. Eligibility: category {item.eligible_category}, min marks required {item.min_marks_required}%, income limit {item.income_limit} INR. Class: {item.min_class} to {item.max_class}."

def build_scheme_text(item) -> str:
    return f"Scheme: {item.scheme_name}. Ministry: {item.ministry}. Benefits: {item.benefits}. Eligibility: category {item.category}, gender {item.gender}, max age {item.max_age}, states {item.states}."

def build_internship_text(item) -> str:
    return f"Internship Sector: {item.sector}. City: {item.location_city}. Duration: {item.duration}. Stipend: {item.stipend_per_month_inr} INR. Mode: {item.mode}."

def backfill_embeddings():
    # Ensure tables exist in the database
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    # Note: get_embedding() uses HuggingFace inference API with offline hash fallback.
    # No API key required — Groq does NOT provide an embeddings endpoint.

    # Seed data from CSV if not loaded
    try:
        print("[BACKFILL] Loading CSV datasets...")
        dataset_loader.load_all()
        dataset_loader.migrate_to_db(db)
    except Exception as e:
        print(f"[BACKFILL WARNING] CSV migration failed or already completed: {e}")

    targets = [
        (College, build_college_text, "Colleges"),
        (Scholarship, build_scholarship_text, "Scholarships"),
        (Scheme, build_scheme_text, "Schemes"),
        (Internship, build_internship_text, "Internships"),
    ]

    try:
        for model_class, text_builder, name in targets:
            collection_name = model_class.__tablename__
            
            # Query all items to ensure Qdrant has all vectors
            items = db.query(model_class).all()
            print(f"[BACKFILL] Processing {len(items)} items in {name}...")
            
            count_new = 0
            count_qdrant = 0
            batch_items = []
            
            for item in items:
                vector = item.embedding
                
                # If embedding doesn't exist in SQL, generate it
                if not vector:
                    text_blob = text_builder(item)
                    vector = get_embedding(text_blob)
                    if vector:
                        item.embedding = vector
                        count_new += 1
                        
                # Upsert to Qdrant if we have a vector
                if vector:
                    import json
                    if isinstance(vector, str):
                        try:
                            vector = json.loads(vector)
                        except Exception:
                            pass
                    
                    payload = {
                        "name": getattr(item, "college_name", None) or getattr(item, "scholarship_name", None) or getattr(item, "scheme_name", None) or getattr(item, "sector", None)
                    }
                    batch_items.append({
                        "id": item.id,
                        "vector": vector,
                        "payload": payload
                    })
                    count_qdrant += 1
                
                # Upload to Qdrant in batches of 100
                if len(batch_items) >= 100:
                    qdrant_service.upsert_opportunity_batch(collection_name, batch_items)
                    batch_items = []
                
                if count_new > 0 and count_new % 50 == 0:
                    db.commit()
            
            # Upsert any remaining items in the batch
            if batch_items:
                qdrant_service.upsert_opportunity_batch(collection_name, batch_items)
                    
            db.commit()
            print(f"[BACKFILL] Completed {name}: generated {count_new} new embeddings, upserted {count_qdrant} to Qdrant.")
    except Exception as e:
        print(f"[BACKFILL ERROR] An unexpected error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill_embeddings()
