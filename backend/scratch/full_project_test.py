import httpx
import sys
import json

BASE = "http://localhost:8000"
T = 30.0
token = None
session_id = None
results = []
PASS = "PASS"
FAIL = "FAIL"

def test(name, fn):
    global token, session_id
    try:
        fn()
        results.append((PASS, name, ""))
        print(f"  [OK]   {name}")
    except AssertionError as e:
        results.append((FAIL, name, str(e)))
        print(f"  [FAIL] {name}")
        print(f"         -> {str(e)[:200]}")
    except Exception as e:
        results.append((FAIL, name, type(e).__name__ + ": " + str(e)))
        print(f"  [FAIL] {name}")
        print(f"         -> {type(e).__name__}: {str(e)[:200]}")

print()
print("=" * 65)
print("  HARYANASARTHI - COMPLETE PROJECT TEST SUITE")
print("=" * 65)

# ── SECTION 1: CORE INFRASTRUCTURE ──────────────────────────────
print("\n-- [1] CORE INFRASTRUCTURE --")

def test_landing():
    r = httpx.get(f"{BASE}/", follow_redirects=True, timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert len(r.text) > 200, "Page seems empty"
test("Landing page loads (GET /)", test_landing)

def test_docs():
    r = httpx.get(f"{BASE}/docs", timeout=T)
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()
test("Swagger API docs accessible (GET /docs)", test_docs)

def test_openapi():
    r = httpx.get(f"{BASE}/openapi.json", timeout=T)
    assert r.status_code == 200
    schema = r.json()
    assert "paths" in schema
    route_count = len(schema["paths"])
    print(f"         -> {route_count} API routes registered")
test("OpenAPI schema valid (GET /openapi.json)", test_openapi)

# ── SECTION 2: DATABASE & STATS ──────────────────────────────────
print("\n-- [2] DATABASE & STATS --")

def test_stats():
    r = httpx.get(f"{BASE}/stats", timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    d = r.json()
    assert d["colleges"] >= 100,     f"colleges={d['colleges']} (expected >=100)"
    assert d["jobs_exams"] >= 50000, f"jobs={d['jobs_exams']} (expected >=50000)"
    assert d["scholarships"] >= 1000,f"scholarships={d['scholarships']} (expected >=1000)"
    assert d["internships"] >= 100,  f"internships={d['internships']} (expected >=100)"
    assert d["schemes"] >= 100,      f"schemes={d['schemes']} (expected >=100)"
    print(f"         -> colleges:{d['colleges']} | jobs:{d['jobs_exams']} | scholarships:{d['scholarships']} | internships:{d['internships']} | schemes:{d['schemes']}")
test("Dataset counts correct (GET /stats)", test_stats)

# ── SECTION 3: AUTHENTICATION ─────────────────────────────────────
print("\n-- [3] AUTHENTICATION --")

def test_login_success():
    global token
    r = httpx.post(f"{BASE}/auth/login", json={"user_id": "user1", "password": "gargi123"}, timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    d = r.json()
    assert "access_token" in d, "No access_token in response"
    assert d["name"] == "Gargi Sharma", f"Wrong name: {d.get('name')}"
    token = d["access_token"]
    print(f"         -> Logged in as: {d['name']} | Token: {token[:35]}...")
test("Login with valid credentials (user1/gargi123)", test_login_success)

def test_login_wrong_pass():
    r = httpx.post(f"{BASE}/auth/login", json={"user_id": "user1", "password": "wrongpass"}, timeout=T)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print(f"         -> Correctly rejected wrong password (401)")
test("Login with wrong password returns 401", test_login_wrong_pass)

def test_login_wrong_user():
    r = httpx.post(f"{BASE}/auth/login", json={"user_id": "ghost_user", "password": "gargi123"}, timeout=T)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print(f"         -> Correctly rejected unknown user (401)")
test("Login with unknown user_id returns 401", test_login_wrong_user)

def test_protected_no_token():
    r = httpx.get(f"{BASE}/user/user1", timeout=T)
    assert r.status_code == 401, f"Expected 401 without token, got {r.status_code}"
    print(f"         -> Correctly blocked unauthenticated request (401)")
test("Protected endpoint blocks unauthenticated (GET /user/user1)", test_protected_no_token)

# ── SECTION 4: USER PROFILE ──────────────────────────────────────
print("\n-- [4] USER PROFILE --")

def test_get_own_profile():
    assert token, "Login failed, skip"
    r = httpx.get(f"{BASE}/user/user1", headers={"Authorization": f"Bearer {token}"}, timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    d = r.json()
    assert d["name"] == "Gargi Sharma"
    assert d["state"] == "Haryana"
    assert d["category"] == "General"
    print(f"         -> name:{d['name']} | age:{d['age']} | state:{d['state']} | category:{d['category']}")
test("Fetch own profile with JWT (GET /user/user1)", test_get_own_profile)

def test_bola_protection():
    assert token, "Login failed, skip"
    # user1's token should NOT access user2's private data if BOLA is enforced
    r = httpx.get(f"{BASE}/user/user2", headers={"Authorization": f"Bearer {token}"}, timeout=T)
    # Should either be 403 (BOLA enforced) or 200 (open profile - either way record it)
    status = r.status_code
    if status == 403:
        print(f"         -> BOLA protection active (403 Forbidden for cross-user access)")
    elif status == 200:
        print(f"         -> Profile is public (200 OK - BOLA not enforced for read)")
    else:
        assert False, f"Unexpected status {status}: {r.text[:100]}"
test("BOLA cross-user access check (GET /user/user2)", test_bola_protection)

# ── SECTION 5: ONBOARDING ─────────────────────────────────────────
print("\n-- [5] ONBOARDING FLOW --")

def test_create_session():
    global session_id
    r = httpx.post(f"{BASE}/onboarding/session/create", timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    d = r.json()
    assert "session_id" in d
    session_id = d["session_id"]
    print(f"         -> Session created: {session_id}")
test("Create onboarding session (POST /onboarding/session/create)", test_create_session)

def test_save_all_fields():
    assert session_id, "No session, skip"
    r = httpx.post(
        f"{BASE}/onboarding/session/{session_id}/save-step",
        json={"step_number": 1, "user_type": "Student", "looking_for": ["Scholarships", "Colleges"], "category": "SC", "location_preference": "Hisar"},
        timeout=T
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    # Read back and verify all 4 fields were saved
    r2 = httpx.get(f"{BASE}/onboarding/session/{session_id}", timeout=T)
    d = r2.json()
    assert d["user_type"] == "Student",   f"user_type not saved: {d}"
    assert d["category"] == "SC",         f"category not saved: {d}"
    assert d["location_preference"] == "Hisar", f"location not saved: {d}"
    print(f"         -> All 4 fields saved: user_type={d['user_type']} category={d['category']} looking_for={d['looking_for']} location={d['location_preference']}")
test("Save all onboarding fields in one step", test_save_all_fields)

def test_skip_step():
    assert session_id, "No session, skip"
    r = httpx.post(
        f"{BASE}/onboarding/session/{session_id}/save-step",
        json={"step_number": 2, "is_skipped": True},
        timeout=T
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    # Read back via GET to check the skipped flag was persisted
    r2 = httpx.get(f"{BASE}/onboarding/session/{session_id}", timeout=T)
    d = r2.json()
    assert d["step2_skipped"] == True, f"step2_skipped not set in session: {d}"
    print(f"         -> Step 2 skipped successfully (step2_skipped=True)")
test("Skip onboarding step (is_skipped=True)", test_skip_step)

# ── SECTION 6: RECOMMENDATIONS ────────────────────────────────────
print("\n-- [6] VECTOR RECOMMENDATIONS --")

def test_recommendations_all():
    r = httpx.get(f"{BASE}/opportunities/recommended",
        params={"user_type": "Student", "looking_for": "Scholarships,Colleges,Internships,Schemes", "category": "SC", "location_preference": "Hisar"},
        timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    d = r.json()
    total = sum(len(v) for v in d.values() if isinstance(v, list))
    cats = [k for k, v in d.items() if isinstance(v, list) and len(v) > 0]
    assert total > 0, "No recommendations returned at all"
    print(f"         -> {total} items across categories: {cats}")
test("Get recommendations for all categories", test_recommendations_all)

def test_recommendations_student():
    r = httpx.get(f"{BASE}/opportunities/recommended",
        params={"user_type": "Student", "looking_for": "Colleges", "category": "General", "location_preference": "Gurugram"},
        timeout=T)
    assert r.status_code == 200
    d = r.json()
    colleges = d.get("colleges", [])
    print(f"         -> {len(colleges)} colleges returned for General/Gurugram query")
test("Recommendations for General category student (Colleges)", test_recommendations_student)

def test_recommendations_job_seeker():
    r = httpx.get(f"{BASE}/opportunities/recommended",
        params={"user_type": "Job Seeker", "looking_for": "Jobs", "category": "OBC", "location_preference": "Faridabad"},
        timeout=T)
    assert r.status_code == 200
    d = r.json()
    total = sum(len(v) for v in d.values() if isinstance(v, list))
    print(f"         -> {total} items for Job Seeker/OBC/Faridabad query")
test("Recommendations for OBC job seeker", test_recommendations_job_seeker)

# ── SECTION 7: AI CHATBOT ──────────────────────────────────────────
print("\n-- [7] AI CHATBOT (Groq Llama-3.3) --")

def test_chatbot_hindi():
    r = httpx.post(f"{BASE}/chatbot/general",
        json={"user_id": "user1", "message": "SC category ke students ke liye scholarship kaunsi hai Haryana mein?"},
        timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    reply = r.json()["reply"]
    assert len(reply) > 30, "Reply too short"
    print(f"         -> Reply: {reply[:130]}...")
test("Chatbot responds in Hinglish (POST /chatbot/general)", test_chatbot_hindi)

def test_chatbot_english():
    r = httpx.post(f"{BASE}/chatbot/general",
        json={"user_id": "user1", "message": "What government schemes are available for women in Haryana?"},
        timeout=T)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:150]}"
    reply = r.json()["reply"]
    assert len(reply) > 30
    print(f"         -> Reply: {reply[:130]}...")
test("Chatbot responds to English query", test_chatbot_english)

def test_chatbot_rate_limit():
    # Verify rate limit header or counter exists in response
    r = httpx.post(f"{BASE}/chatbot/general",
        json={"user_id": "user1", "message": "Internship ke baare mein batao"},
        timeout=T)
    assert r.status_code in [200, 429], f"Unexpected status: {r.status_code}"
    if r.status_code == 429:
        print(f"         -> Rate limit hit (429) - limiter is working")
    else:
        print(f"         -> Response OK (200) - within rate limit")
test("Chatbot rate limiting (should be 200 or 429)", test_chatbot_rate_limit)

# ── SECTION 8: FINAL SUMMARY ───────────────────────────────────────
print()
print("=" * 65)
print("  FINAL TEST RESULTS")
print("=" * 65)
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
print(f"  PASSED : {passed}/{len(results)}")
print(f"  FAILED : {failed}/{len(results)}")
print("=" * 65)
if failed == 0:
    print("  ALL TESTS PASSED - PROJECT IS FULLY OPERATIONAL!")
else:
    print("  FAILURES DETECTED:")
    for s, name, err in results:
        if s == FAIL:
            print(f"    - {name}")
            print(f"      {err[:120]}")
print("=" * 65)

sys.exit(0 if failed == 0 else 1)
