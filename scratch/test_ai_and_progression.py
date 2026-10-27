import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:5291/api"

def make_request(url, method="GET", data=None, token=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    body = json.dumps(data).encode("utf-8") if data else None
    try:
        with urllib.request.urlopen(req, data=body) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except:
            return e.code, {"error": err_body}

def main():
    print("=== 1. AUTHENTICATION TEST ===")
    status, res = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": "student@learnova.ai",
        "password": "Student@123"
    })
    assert status == 200, f"Login failed: {res}"
    token = res["token"]
    print("✓ Successfully authenticated student@learnova.ai")

    print("\n=== 2. AI ASSISTANT: 11 QUESTIONS CONVERSATIONAL TEST ===")
    questions = [
        "What is TCP?",
        "Explain TCP vs UDP.",
        "What is Big O?",
        "Explain merge sort.",
        "What is supervised learning?",
        "Explain K-Means.",
        "What is an 8085 microprocessor?",
        "Explain JWT.",
        "What is ASP.NET Core middleware?",
        "What is the difference between data mining and data science?",
        "Explain recursion with an example."
    ]

    history = []
    for i, q in enumerate(questions, 1):
        status, chat_res = make_request(f"{BASE_URL}/ai/chat", method="POST", data={
            "message": q,
            "history": history
        }, token=token)

        assert status == 200, f"Chat question {i} failed: {chat_res}"
        reply = chat_res.get("reply", "")
        assert len(reply) > 20, f"Reply too short: {reply}"
        print(f"[{i}/11] Q: {q}")
        print(f"      A: {reply[:100]}... (Length: {len(reply)} chars)")

        history.append({"role": "user", "text": q})
        history.append({"role": "model", "text": reply})

    print("✓ Successfully asked 11 consecutive questions without artificial limit!")

    print("\n=== 3. SEQUENTIAL COURSE UNLOCKING & BACKEND SECURITY ENFORCEMENT ===")
    status, courses = make_request(f"{BASE_URL}/courses")
    assert status == 200 and len(courses) > 0, "No courses found"
    test_course = courses[0]
    course_id = test_course["id"]
    print(f"Testing with course: '{test_course['title']}' (ID: {course_id})")

    # Step A: Enroll in course
    status, enroll_res = make_request(f"{BASE_URL}/courses/{course_id}/enroll", method="POST", token=token)
    assert status == 200, f"Enroll failed: {enroll_res}"
    print(f"✓ Student enrolled successfully")

    # Step B: Check Initial Progress
    status, prog = make_request(f"{BASE_URL}/courses/{course_id}/progress", token=token)
    assert status == 200, f"Progress failed: {prog}"
    chaps = test_course.get("chapters", [])
    mod1 = chaps[0]
    l1 = mod1["lessons"][0]
    l2 = mod1["lessons"][1]
    mod2 = chaps[1] if len(chaps) > 1 else None

    print(f"Module 1 ID: {mod1['id']}, Lesson 1 ID: {l1['id']}, Lesson 2 ID: {l2['id']}")
    print(f"Unlocked Chapters: {prog['unlockedChapterIds']}")
    print(f"Unlocked Lessons: {prog['unlockedLessonIds']}")

    assert mod1["id"] in prog["unlockedChapterIds"], "Module 1 must be unlocked initially"
    assert l1["id"] in prog["unlockedLessonIds"], "Lesson 1 must be unlocked initially"
    assert l2["id"] not in prog["unlockedLessonIds"], "Lesson 2 MUST be locked initially"
    if mod2:
        assert mod2["id"] not in prog["unlockedChapterIds"], "Module 2 MUST be locked initially"
    print("✓ Initial state verified: Module 1 Lesson 1 unlocked, Lesson 2 & Module 2 locked")

    # Step C: URL MANIPULATION ATTACK TEST (Attempt to fetch locked Lesson 2)
    print("\nAttempting direct URL manipulation on locked Lesson 2...")
    status, locked_res = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l2['id']}", token=token)
    print(f"Backend response status: {status}")
    print(f"Backend response body: {locked_res}")
    assert status == 403, f"Expected 403 Forbidden for locked lesson, got {status}"
    assert locked_res.get("isLocked") == True, "Lesson must be marked locked"
    assert locked_res.get("videoUrl") is None, "VideoUrl MUST be scrubbed when locked"
    print("✓ Backend security verified: Direct API access to locked lesson rejected with 403 Forbidden and scrubbed media!")

    # Step D: Complete Lesson 1
    print(f"\nCompleting Lesson 1 ({l1['title']})...")
    status, comp_res = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l1['id']}/complete", method="POST", token=token)
    assert status == 200 and comp_res["success"], f"Complete failed: {comp_res}"
    print(f"✓ Lesson 1 completed. Reported NextLessonId: {comp_res.get('nextLessonId')}")

    # Step E: Verify Lesson 2 is now unlocked
    status, prog2 = make_request(f"{BASE_URL}/courses/{course_id}/progress", token=token)
    assert l2["id"] in prog2["unlockedLessonIds"], "Lesson 2 should now be unlocked!"
    print(f"✓ Verified Lesson 2 is now unlocked! Progress: {prog2['progressPercent']}%")

    # Step F: Verify Lesson 2 protected content is now accessible
    status, l2_data = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l2['id']}", token=token)
    assert status == 200 and not l2_data.get("isLocked"), "Lesson 2 should now return 200 OK and be unlocked"
    assert l2_data.get("videoUrl") is not None, "Lesson 2 videoUrl should now be accessible"
    print("✓ Verified Lesson 2 protected content and videoUrl are now accessible!")

    # Step G: Test completing remaining lessons of Module 1 to test Module 2 unlocking
    print("\nCompleting remaining lessons in Module 1 to verify Module 2 unlock...")
    for remaining_les in mod1["lessons"][1:]:
        make_request(f"{BASE_URL}/courses/{course_id}/lessons/{remaining_les['id']}/complete", method="POST", token=token)

    status, prog3 = make_request(f"{BASE_URL}/courses/{course_id}/progress", token=token)
    if mod2:
        assert mod2["id"] in prog3["unlockedChapterIds"], "Module 2 MUST be unlocked after all Module 1 lessons completed!"
        mod2_l1 = mod2["lessons"][0]
        assert mod2_l1["id"] in prog3["unlockedLessonIds"], "Module 2 Lesson 1 MUST be unlocked!"
        print(f"✓ Verified Module 2 ({mod2['title']}) and its first lesson ({mod2_l1['title']}) are now unlocked!")

    print("\n=== 4. RECOMMENDATIONS GROUNDED IN REAL PROGRESS ===")
    status, rec_res = make_request(f"{BASE_URL}/ai/recommendations", token=token)
    assert status == 200, f"Recommendations failed: {rec_res}"
    assert rec_res.get("hasData") == True, "Student now has real progress so recommendations must have data"
    recs = rec_res.get("recommendations", [])
    print(f"Recommendations count: {len(recs)}")
    for r in recs:
        print(f"- [{r.get('type')}] {r.get('title')}: {r.get('reason')}")
    print("✓ Recommendations successfully generated and grounded in real student data!")

    print("\n==============================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==============================================")

if __name__ == "__main__":
    main()
