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
    body = json.dumps(data).encode("utf-8") if data is not None else None
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
    print("=================================================================")
    print("TEST SUITE: REAL VIDEO COMPLETION & BACKEND SECURITY VERIFICATION")
    print("=================================================================")

    # 1. Login
    status, login_res = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": "demo.student@learnova.ai",
        "password": "Student@123"
    })
    assert status == 200, f"Login failed: {login_res}"
    token = login_res["token"]
    print("✓ Successfully authenticated demo.student@learnova.ai")

    # 2. Get Courses
    status, courses = make_request(f"{BASE_URL}/courses")
    assert status == 200 and len(courses) > 0, "No courses found"
    test_course = courses[1] # Choose Computer Networks
    course_id = test_course["id"]
    print(f"Testing with course: '{test_course['title']}' (ID: {course_id})")

    # 3. Enroll
    status, enroll_res = make_request(f"{BASE_URL}/courses/{course_id}/enroll", method="POST", token=token)
    assert status == 200, f"Enrollment failed: {enroll_res}"
    print("✓ Student enrolled in course")

    # 4. Check initial progress: Lesson 1 unlocked, Lesson 2 locked
    status, prog = make_request(f"{BASE_URL}/courses/{course_id}/progress", token=token)
    l1 = test_course["chapters"][0]["lessons"][0]
    l2 = test_course["chapters"][0]["lessons"][1]
    assert l1["id"] in prog["unlockedLessonIds"], "Lesson 1 must be unlocked"
    assert l2["id"] not in prog["unlockedLessonIds"], "Lesson 2 must be locked"
    print(f"✓ Initial unlock verified: Lesson 1 ({l1['id']}) unlocked, Lesson 2 ({l2['id']}) locked")

    # TEST A: ATTEMPT TO MARK LESSON 1 AS COMPLETED WITHOUT WATCHING VIDEO
    print("\n--- TEST A: Video Completion Bypass Attack ---")
    print("Attempting to call POST complete on Lesson 1 with 0% watched time...")
    status, bypass_res = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l1['id']}/complete", method="POST", data={}, token=token)
    print(f"Status: {status}, Response: {bypass_res}")
    assert status == 400, f"Expected 400 Bad Request, got {status}"
    assert "requirement not met" in str(bypass_res).lower() or "90%" in str(bypass_res), f"Unexpected error message: {bypass_res}"
    print("✓ TEST A PASSED: Backend strictly rejected immediate completion without video watch!")

    # TEST B: ATTEMPT COMPLETION WITH INSUFFICIENT WATCHED TIME (e.g. 35%)
    print("\n--- TEST B: Insufficient Watched Time Attack (35%) ---")
    status, prog_update = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l1['id']}/video-progress", method="POST", data={
        "watchedSeconds": 350,
        "videoDuration": 1000,
        "watchedPercentage": 35,
        "lastPositionSeconds": 350
    }, token=token)
    assert status == 200 and not prog_update.get("videoRequirementCompleted"), "Requirement should NOT be completed at 35%"

    status, ins_res = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l1['id']}/complete", method="POST", data={}, token=token)
    print(f"Status: {status}, Response: {ins_res}")
    assert status == 400, f"Expected 400 Bad Request at 35% watch, got {status}"
    print("✓ TEST B PASSED: Backend strictly rejected completion when watched time is only 35%!")

    # TEST C: DIRECT URL MANIPULATION ATTACK ON LOCKED LESSON 2
    print("\n--- TEST C: Direct URL / API Bypass on Locked Lesson 2 ---")
    status, locked_res = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l2['id']}", token=token)
    print(f"Status: {status}, Response: {locked_res}")
    assert status == 403, f"Expected 403 Forbidden for locked lesson, got {status}"
    assert locked_res.get("isLocked") == True, "Lesson must be reported as locked"
    assert locked_res.get("videoUrl") is None, "Video URL must be scrubbed when locked"
    print("✓ TEST C PASSED: Direct access to locked lesson rejected with 403 Forbidden and scrubbed video!")

    # TEST D: GENUINE WATCH TIME REACHES 92% (THRESHOLD MET)
    print("\n--- TEST D: Legitimate Playback Reaches 92% (>= 90%) ---")
    status, prog_ok = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l1['id']}/video-progress", method="POST", data={
        "watchedSeconds": 920,
        "videoDuration": 1000,
        "watchedPercentage": 92,
        "lastPositionSeconds": 920
    }, token=token)
    assert status == 200 and prog_ok.get("videoRequirementCompleted"), "Requirement SHOULD be met at 92%"
    print("✓ Video progress recorded with videoRequirementCompleted = True")

    # TEST E: COMPLETE LESSON 1 WITH VERIFIED 92% WATCH TIME
    print("\n--- TEST E: Legitimate Completion of Lesson 1 ---")
    status, comp_res = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l1['id']}/complete", method="POST", data={}, token=token)
    assert status == 200 and comp_res.get("success"), f"Legitimate completion failed: {comp_res}"
    print(f"✓ Lesson 1 completed successfully! Next lesson: {comp_res.get('nextLessonId')}")

    # TEST F: VERIFY LESSON 2 IS NOW UNLOCKED
    print("\n--- TEST F: Verify Sequential Unlock of Lesson 2 ---")
    status, prog_after = make_request(f"{BASE_URL}/courses/{course_id}/progress", token=token)
    assert l2["id"] in prog_after["unlockedLessonIds"], "Lesson 2 should now be unlocked"
    status, l2_data = make_request(f"{BASE_URL}/courses/{course_id}/lessons/{l2['id']}", token=token)
    assert status == 200 and not l2_data.get("isLocked"), "Lesson 2 should now be accessible"
    assert l2_data.get("videoUrl") is not None, "Lesson 2 videoUrl should now be delivered"
    print(f"✓ Lesson 2 is now unlocked and accessible with video URL!")

    print("\n=================================================================")
    print("ALL VIDEO COMPLETION & ANTI-BYPASS SECURITY TESTS PASSED (100%)!")
    print("=================================================================")

if __name__ == "__main__":
    main()
