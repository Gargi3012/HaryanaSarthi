import httpx
import sys

BASE = "http://localhost:8000"
results = []
token = None
session_id = None
T = 30.0  # 30s timeout — Neon DB cold-start can be slow


def check(name, fn):
    try:
        fn()
        results.append(("PASS", name, ""))
    except Exception as e:
        results.append(("FAIL", name, str(e)))


# TEST 1: Landing page
def t1():
    r = httpx.get(f"{BASE}/", follow_redirects=True, timeout=T)
    assert r.status_code == 200, f"Status {r.status_code}"
    assert len(r.text) > 100, "Empty page"
check("Landing page  GET /", t1)

# TEST 2: Stats API
def t2():
    r = httpx.get(f"{BASE}/stats", timeout=T)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    d = r.json()
    assert d["colleges"] > 0
    assert d["jobs_exams"] > 0
    assert d["scholarships"] > 0
    print(f"         Stats -> colleges:{d['colleges']} jobs:{d['jobs_exams']} scholarships:{d['scholarships']}")
check("Stats API  GET /stats", t2)

# TEST 3: Login
def t3():
    global token
    r = httpx.post(f"{BASE}/auth/login", json={"user_id": "user1", "password": "gargi123"}, timeout=T)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    d = r.json()
    token = d["access_token"]
    print(f"         Login OK -> name:{d['name']}  token:{token[:30]}...")
check("JWT Login  POST /auth/login", t3)

# TEST 4: Secured profile (depends on token from TEST 3)
def t4():
    assert token, "No token — login must have failed"
    r = httpx.get(f"{BASE}/user/user1", headers={"Authorization": f"Bearer {token}"}, timeout=T)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    d = r.json()
    print(f"         Profile -> name:{d['name']} state:{d['state']} category:{d['category']}")
check("BOLA Profile  GET /user/user1", t4)

# TEST 5: Onboarding session + save step
def t5():
    global session_id
    r = httpx.post(f"{BASE}/onboarding/session/create", timeout=T)
    assert r.status_code == 200, f"Create session failed: {r.text}"
    session_id = r.json()["session_id"]
    r2 = httpx.post(
        f"{BASE}/onboarding/session/{session_id}/save-step",
        json={
            "step_number": 1,
            "user_type": "Student",
            "looking_for": ["Scholarships", "Colleges"],
            "category": "SC",
            "location_preference": "Hisar"
        },
        timeout=T
    )
    assert r2.status_code == 200, f"Save step failed: {r2.text}"
    r3 = httpx.get(f"{BASE}/onboarding/session/{session_id}", timeout=T)
    d = r3.json()
    assert d["user_type"] == "Student", f"user_type not saved: {d}"
    assert d["category"] == "SC", f"category not saved: {d}"
    print(f"         Session -> {session_id}  user_type:{d['user_type']} category:{d['category']} location:{d['location_preference']}")
check("Onboarding create + multi-field save", t5)

# TEST 6: Recommendations
def t6():
    r = httpx.get(
        f"{BASE}/opportunities/recommended",
        params={"user_type": "Student", "looking_for": "Scholarships,Colleges", "category": "SC", "location_preference": "Hisar"},
        timeout=T
    )
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    d = r.json()
    total = sum(len(v) for v in d.values() if isinstance(v, list))
    assert total > 0, "No recommendations returned"
    print(f"         Recommendations -> {total} items  categories: {list(d.keys())}")
check("Vector Recommendations  GET /opportunities/recommended", t6)

# TEST 7: Groq Chatbot
def t7():
    r = httpx.post(
        f"{BASE}/chatbot/general",
        json={"user_id": "user1", "message": "SC students ke liye scholarship batao"},
        timeout=T
    )
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    reply = r.json()["reply"]
    assert len(reply) > 20, "Empty chatbot reply"
    print(f"         Chatbot -> {reply[:120]}...")
check("Groq Chatbot  POST /chatbot/general", t7)

# TEST 8: Swagger Docs
def t8():
    r = httpx.get(f"{BASE}/docs", timeout=T)
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()
check("Swagger API Docs  GET /docs", t8)

# ── Results ──────────────────────────────────────────────
print()
print("=" * 60)
print("  HARYANASARTHI  LIVE SERVER  FULL TEST RESULTS")
print("=" * 60)
for status, name, err in results:
    icon = "[OK]  " if status == "PASS" else "[FAIL]"
    line = f"  {icon}  {name}"
    if err:
        line += f"\n           ERROR: {err[:150]}"
    print(line)
print("=" * 60)
passed = sum(1 for s, _, _ in results if s == "PASS")
print(f"  {passed}/{len(results)} TESTS PASSED")
print("=" * 60)

if passed < len(results):
    sys.exit(1)
