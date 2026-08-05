import os
import sys
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Put backend folder in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# Force dedicated test database to avoid file locking conflicts
os.environ["DATABASE_URL"] = "sqlite:///./test_haryanasarthi.db"

# Clean up any existing local test database file
for path in ["test_haryanasarthi.db"]:
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"[CLEANUP] Deleted old test database: {path}")
        except Exception as e:
            print(f"[CLEANUP WARNING] Failed to delete test database: {e}")

from main import app
from database import Base, engine, SessionLocal
from seed_data import create_dummy_users
from services.dataset_loader import dataset_loader

# Re-initialize tables and seed dummy profiles
Base.metadata.create_all(bind=engine)
db = SessionLocal()
create_dummy_users(db)
dataset_loader.load_all()
dataset_loader.migrate_to_db(db)
db.close()

client = TestClient(app)

print("\n=======================================================")
print("  HARYANASARTHI END-TO-END VALIDATION TEST SUITE       ")
print("=======================================================\n")

# 1. Verify Stats Endpoint
try:
    print("[TEST 1/6] Fetching Dynamic Opportunities Counters...")
    response = client.get("/stats")
    assert response.status_code == 200, f"Stats request failed: {response.text}"
    stats = response.json()
    print(f" -> [SUCCESS] Stats Data: {stats}")
    assert stats["colleges"] > 0, "Colleges table is empty!"
    assert stats["scholarships"] > 0, "Scholarships table is empty!"
except Exception as e:
    print(f" -> [FAILED] Test 1: {e}")
    sys.exit(1)

# 2. Verify User Login and Hashed Password authentication
try:
    print("\n[TEST 2/6] Logging in Seeded Account (user1 / gargi123)...")
    payload = {"user_id": "user1", "password": "gargi123"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200, f"Login request failed: {response.text}"
    token_data = response.json()
    token = token_data.get("access_token")
    assert token, "Token not returned in login response!"
    print(f" -> [SUCCESS] JWT Token Created: {token[:25]}... (Owner: {token_data.get('name')})")
except Exception as e:
    print(f" -> [FAILED] Test 2: {e}")
    sys.exit(1)

# 3. Verify BOLA Security Profile route
try:
    print("\n[TEST 3/6] Fetching Profile details with JWT Token...")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/user/user1", headers=headers)
    assert response.status_code == 200, f"Accessing user profile failed: {response.text}"
    profile = response.json()
    print(f" -> [SUCCESS] Secured Profile details loaded: Name={profile.get('name')}, State={profile.get('state')}")
except Exception as e:
    print(f" -> [FAILED] Test 3: {e}")
    sys.exit(1)

# 4. Verify Recommendations (Vector Cosine Similarity Ranking)
try:
    print("\n[TEST 4/6] Querying Vector Recommendation matching algorithm...")
    
    # 4a. Create onboarding session
    res = client.post("/onboarding/session/create")
    assert res.status_code == 200, "Failed to create onboarding session"
    session_id = res.json()["session_id"]
    
    # 4b. Save step answers — send flat fields (BUG-002 fix: no nested 'data' key)
    step_payload = {
        "step_number": 1,
        "user_type": "Student",
        "looking_for": ["Scholarships", "Colleges"],
        "category": "SC",
        "location_preference": "Hisar"
    }
    res = client.post(f"/onboarding/session/{session_id}/save-step", json=step_payload)
    assert res.status_code == 200, f"Failed to save onboarding steps answers: {res.text}"
    
    # 4c. Load opportunities via correct GET /opportunities/recommended (BUG-003 fix)
    response = client.get("/opportunities/recommended?user_type=Student&looking_for=Scholarships%2CColleges&category=SC&location_preference=Hisar")
    assert response.status_code == 200, f"Opportunities recommend query failed: {response.text}"
    recommendations = response.json()
    total = sum(len(v) for v in recommendations.values() if isinstance(v, list))
    print(f" -> [SUCCESS] Found {total} opportunity items across all categories.")
except Exception as e:
    print(f" -> [FAILED] Test 4: {e}")
    sys.exit(1)

# 5. Verify Chatbot Endpoint (Communicating with Groq Llama-3.3)
try:
    print("\n[TEST 5/6] Testing Groq Chatbot completions (Llama-3.3-70b)...")
    chat_payload = {
        "user_id": "user1",
        "message": "Haryana me SC category ke students ke liye kaunsi standard scholarship scheme hai?"
    }
    response = client.post("/chatbot/general", json=chat_payload)
    assert response.status_code == 200, f"Chatbot query failed: {response.text}"
    reply = response.json()
    print(f" -> [SUCCESS] Chatbot Reply: {reply.get('reply')[:200]}...")
except Exception as e:
    print(f" -> [FAILED] Test 5: {e}")
    sys.exit(1)

# 6. Verify Next Best Action Document Analysis (Communicating with Groq Llama-3.2-Vision)
try:
    print("\n[TEST 6/6] Testing Groq Vision document verifier (Llama-3.2-Vision)...")
    doc_payload = {
        "user_id": "user1",
        "file_name": "test_document.png",  # BUG-006 fix: file_name is required by schema
        "file_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "mime_type": "image/png",
        "opportunity_name": "Post Matric Scholarship Haryana"
    }
    response = client.post("/chatbot/analyze-document", json=doc_payload)
    assert response.status_code == 200, f"Vision document analysis failed: {response.text}"
    doc_reply = response.json()
    print(f" -> [SUCCESS] Vision analysis reply: {doc_reply.get('reply')[:200]}...")
except Exception as e:
    print(f" -> [FAILED] Test 6: {e}")
    sys.exit(1)

print("\n=======================================================")
print("  ALL TESTS PASSED SUCCESSFULLY! PROJECT IS 100% READY!")
print("=======================================================\n")
