import urllib.request
import urllib.error
import json
import time
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

def run_tests():
    print("=" * 70)
    print("AI-LMS COMPREHENSIVE MULTI-USER DATA ISOLATION & PROGRESS SUITE")
    print("=" * 70)

    ts = int(time.time())
    email_a = f"student_a_{ts}@learnova.ai"
    email_b = f"student_b_{ts}@learnova.ai"
    password = "Student@123"

    # =========================================================================
    # SCENARIO A: NEW STUDENT REGISTRATION & CLEAN ISOLATION
    # =========================================================================
    print("\n[SCENARIO A] Registering Student A and verifying pristine initial state...")
    st, reg_a = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "Student Alpha",
        "email": email_a,
        "password": password
    })
    assert st == 200, f"Register A failed: {reg_a}"
    student_a_id = reg_a["userId"]
    print(f"✓ Registered Student A: {email_a} (ID: {student_a_id})")

    st, login_a = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": email_a,
        "password": password
    })
    assert st == 200, f"Login A failed: {login_a}"
    token_a = login_a["token"]
    print("✓ Successfully authenticated Student A")

    # Confirm My Courses is empty
    st, enrolled_a = make_request(f"{BASE_URL}/courses/enrolled", token=token_a)
    assert st == 200, f"Get enrolled failed: {enrolled_a}"
    assert len(enrolled_a) == 0, f"Expected 0 enrollments for new student, got {len(enrolled_a)}"
    print("✓ VERIFIED: Student A has exactly 0 enrolled courses.")

    # Confirm certificates is empty
    st, certs_a = make_request(f"{BASE_URL}/certificates/my", token=token_a)
    assert st == 200, f"Get certs failed: {certs_a}"
    assert len(certs_a) == 0, f"Expected 0 certificates for new student, got {len(certs_a)}"
    print("✓ VERIFIED: Student A has exactly 0 certificates.")

    # Confirm Browse Courses lists catalog
    st, courses = make_request(f"{BASE_URL}/courses")
    assert st == 200 and len(courses) >= 6, f"Courses catalog lookup failed: {courses}"
    print(f"✓ VERIFIED: Browse Courses lists full academic catalog ({len(courses)} courses).")

    # =========================================================================
    # SCENARIO B: ENROLLMENT OF STUDENT A
    # =========================================================================
    print("\n[SCENARIO B] Enrolling Student A into Course X...")
    course_x = courses[0]
    course_x_id = course_x["id"]
    course_x_title = course_x["title"]
    print(f"Target Course: '{course_x_title}' (ID: {course_x_id})")

    st, enr_res = make_request(f"{BASE_URL}/courses/{course_x_id}/enroll", method="POST", token=token_a)
    assert st == 200, f"Enroll failed: {enr_res}"
    print(f"✓ Student A enrolled in Course X: {enr_res.get('courseTitle')}")

    # Verify Student A now sees Course X in My Courses with 0% progress
    st, enrolled_a_after = make_request(f"{BASE_URL}/courses/enrolled", token=token_a)
    assert len(enrolled_a_after) == 1, f"Expected 1 enrolled course, got {len(enrolled_a_after)}"
    assert enrolled_a_after[0]["courseId"] == course_x_id, "Enrolled courseId mismatch"
    assert enrolled_a_after[0]["progressPercent"] == 0, f"Progress must start at 0, got {enrolled_a_after[0]['progressPercent']}"
    print("✓ VERIFIED: Course X appears in Student A's My Courses with starting progress = 0%.")

    # Verify duplicate enrollment is prevented gracefully
    st, enr_dup = make_request(f"{BASE_URL}/courses/{course_x_id}/enroll", method="POST", token=token_a)
    assert st == 200, "Duplicate enrollment attempt should succeed idempotently"
    st, enrolled_check = make_request(f"{BASE_URL}/courses/enrolled", token=token_a)
    assert len(enrolled_check) == 1, f"Duplicate enrollment created extra record! Count: {len(enrolled_check)}"
    print("✓ VERIFIED: Duplicate enrollment prevented by compound uniqueness.")

    # =========================================================================
    # SCENARIO C: PROGRESS ADVANCEMENT & TWO-STUDENT ISOLATION
    # =========================================================================
    print("\n[SCENARIO C] Advancing Student A progress and registering Student B...")
    l1 = course_x["chapters"][0]["lessons"][0]
    l2 = course_x["chapters"][0]["lessons"][1]

    # Student A completes Lesson 1 (video watch >= 90% then complete)
    st, vp1 = make_request(f"{BASE_URL}/courses/{course_x_id}/lessons/{l1['id']}/video-progress", method="POST", data={
        "watchedSeconds": 950,
        "videoDuration": 1000,
        "watchedPercentage": 95,
        "lastPositionSeconds": 950
    }, token=token_a)
    assert st == 200 and vp1.get("videoRequirementCompleted"), "Video requirement should be met"

    st, comp1 = make_request(f"{BASE_URL}/courses/{course_x_id}/lessons/{l1['id']}/complete", method="POST", token=token_a)
    assert st == 200 and comp1.get("success"), f"Lesson 1 completion failed: {comp1}"
    print(f"✓ Student A completed Lesson 1 ({l1['title']})")

    # Student A completes Lesson 2
    st, vp2 = make_request(f"{BASE_URL}/courses/{course_x_id}/lessons/{l2['id']}/video-progress", method="POST", data={
        "watchedSeconds": 920,
        "videoDuration": 1000,
        "watchedPercentage": 92,
        "lastPositionSeconds": 920
    }, token=token_a)
    assert st == 200 and vp2.get("videoRequirementCompleted"), "Video requirement 2 should be met"

    st, comp2 = make_request(f"{BASE_URL}/courses/{course_x_id}/lessons/{l2['id']}/complete", method="POST", token=token_a)
    assert st == 200 and comp2.get("success"), f"Lesson 2 completion failed: {comp2}"
    print(f"✓ Student A completed Lesson 2 ({l2['title']})")

    # Check Student A's progress state
    st, prog_a = make_request(f"{BASE_URL}/courses/{course_x_id}/progress", token=token_a)
    assert prog_a["completedLessonsCount"] == 2, f"Student A should have 2 completed lessons, got {prog_a['completedLessonsCount']}"
    assert l1["id"] in prog_a["completedLessonIds"] and l2["id"] in prog_a["completedLessonIds"]
    progress_pct_a = prog_a["progressPercent"]
    print(f"✓ Student A progress recorded: {prog_a['completedLessonsCount']} completed lessons ({progress_pct_a}%)")

    # Register Student B
    print("\nRegistering Student B...")
    st, reg_b = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "Student Beta",
        "email": email_b,
        "password": password
    })
    assert st == 200, f"Register B failed: {reg_b}"
    student_b_id = reg_b["userId"]

    st, login_b = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": email_b,
        "password": password
    })
    assert st == 200, f"Login B failed: {login_b}"
    token_b = login_b["token"]
    print(f"✓ Registered and authenticated Student B: {email_b}")

    # Confirm Student B sees NO inherited enrollment or progress
    st, enrolled_b = make_request(f"{BASE_URL}/courses/enrolled", token=token_b)
    assert len(enrolled_b) == 0, f"Student B must have 0 enrollments, found: {enrolled_b}"
    print("✓ VERIFIED: Student B has 0 enrollments (did NOT inherit Student A's enrollment).")

    st, prog_b_pre = make_request(f"{BASE_URL}/courses/{course_x_id}/progress", token=token_b)
    assert not prog_b_pre["isEnrolled"], "Student B must not be enrolled in Course X yet"
    assert prog_b_pre["completedLessonsCount"] == 0, "Student B must have 0 completed lessons"
    assert len(prog_b_pre["completedLessonIds"]) == 0, "Student B completedLessonIds must be empty"
    print("✓ VERIFIED: Student B sees 0 progress on Course X prior to enrollment.")

    # Student B enrolls in Course X
    print("\nEnrolling Student B in Course X...")
    st, enr_b_res = make_request(f"{BASE_URL}/courses/{course_x_id}/enroll", method="POST", token=token_b)
    assert st == 200, f"Student B enrollment failed: {enr_b_res}"

    st, prog_b_post = make_request(f"{BASE_URL}/courses/{course_x_id}/progress", token=token_b)
    assert prog_b_post["isEnrolled"], "Student B should be enrolled"
    assert prog_b_post["completedLessonsCount"] == 0, f"Student B must start with 0 completed lessons, got {prog_b_post['completedLessonsCount']}"
    assert prog_b_post["progressPercent"] == 0, f"Student B must start with 0% progress, got {prog_b_post['progressPercent']}"
    assert l1["id"] in prog_b_post["unlockedLessonIds"], "Lesson 1 should be unlocked for Student B"
    assert l2["id"] not in prog_b_post["unlockedLessonIds"], "Lesson 2 MUST BE LOCKED for Student B (sequential isolation)"
    print("✓ VERIFIED: Student B starts with 0% progress, Lesson 1 unlocked, Lesson 2 locked.")

    # Student B completes Lesson 1 only
    st, vp_b1 = make_request(f"{BASE_URL}/courses/{course_x_id}/lessons/{l1['id']}/video-progress", method="POST", data={
        "watchedSeconds": 910,
        "videoDuration": 1000,
        "watchedPercentage": 91,
        "lastPositionSeconds": 910
    }, token=token_b)
    assert st == 200

    st, comp_b1 = make_request(f"{BASE_URL}/courses/{course_x_id}/lessons/{l1['id']}/complete", method="POST", token=token_b)
    assert st == 200

    st, prog_b_final = make_request(f"{BASE_URL}/courses/{course_x_id}/progress", token=token_b)
    assert prog_b_final["completedLessonsCount"] == 1, f"Student B should have 1 completed lesson, got {prog_b_final['completedLessonsCount']}"
    print("✓ Student B has completed 1 lesson.")

    # Re-verify Student A still has 2 completed lessons and unaffected progress
    st, prog_a_final = make_request(f"{BASE_URL}/courses/{course_x_id}/progress", token=token_a)
    assert prog_a_final["completedLessonsCount"] == 2, f"Student A progress was corrupted! Expected 2, got {prog_a_final['completedLessonsCount']}"
    assert prog_a_final["progressPercent"] == progress_pct_a, "Student A progress percentage changed!"
    print(f"✓ VERIFIED: Student A still has 2 completed lessons ({progress_pct_a}%), Student B has 1 completed lesson.")

    # =========================================================================
    # SCENARIO D: AUTHORIZATION & BOUNDARY SECURITY
    # =========================================================================
    print("\n[SCENARIO D] Testing Cross-User Authorization and Boundary Controls...")

    # 1. Unauthenticated requests rejected
    st_unauth, _ = make_request(f"{BASE_URL}/courses/enrolled")
    assert st_unauth == 401, f"Expected 401 for unauthenticated enrolled query, got {st_unauth}"
    print("✓ VERIFIED: Unauthenticated access to /courses/enrolled returns HTTP 401.")

    st_unauth_cert, _ = make_request(f"{BASE_URL}/certificates/my")
    assert st_unauth_cert == 401, f"Expected 401 for unauthenticated certificates query, got {st_unauth_cert}"
    print("✓ VERIFIED: Unauthenticated access to /certificates/my returns HTTP 401.")

    # 2. Student B cannot complete a lesson for a course they are NOT enrolled in
    course_y_id = courses[2]["id"] # A course Student B is not enrolled in
    l_y1_id = courses[2]["chapters"][0]["lessons"][0]["id"]
    st_unenrolled_comp, res_un = make_request(f"{BASE_URL}/courses/{course_y_id}/lessons/{l_y1_id}/complete", method="POST", token=token_b)
    assert st_unenrolled_comp == 403, f"Expected 403 Forbidden for completing lesson on unenrolled course, got {st_unenrolled_comp}"
    print("✓ VERIFIED: Attempting lesson completion on unenrolled course rejected with HTTP 403.")

    # 3. Student B cannot access private certificate of another student
    # Check if any certificate exists in system
    st, admin_login = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": "admin@learnova.ai",
        "password": "Admin@123"
    })
    if st == 200:
        admin_token = admin_login["token"]
        st, all_certs = make_request(f"{BASE_URL}/certificates/admin", token=admin_token)
        if st == 200 and len(all_certs) > 0:
            other_cert = all_certs[0]
            other_cert_id = other_cert["id"]
            if other_cert.get("studentId") != student_b_id:
                # Student B attempts to fetch other student's private certificate
                st_cross_cert, cross_res = make_request(f"{BASE_URL}/certificates/{other_cert_id}", token=token_b)
                assert st_cross_cert == 403, f"Expected 403 Forbidden when accessing another student's certificate, got {st_cross_cert}"
                print(f"✓ VERIFIED: Cross-student private certificate access strictly rejected with HTTP 403: {cross_res.get('message')}")

    # =========================================================================
    # SCENARIO E: ACCOUNT SWITCHING SCOPING
    # =========================================================================
    print("\n[SCENARIO E] Verifying complete scoping during account switching...")
    # Fetch with Token A
    st, enr_switch_a = make_request(f"{BASE_URL}/courses/enrolled", token=token_a)
    # Fetch with Token B
    st, enr_switch_b = make_request(f"{BASE_URL}/courses/enrolled", token=token_b)

    assert len(enr_switch_a) == 1 and enr_switch_a[0]["progressPercent"] == progress_pct_a
    assert len(enr_switch_b) == 1 and enr_switch_b[0]["progressPercent"] < progress_pct_a
    print("✓ VERIFIED: User sessions are completely scoped by token; switching user never leaks data.")

    # =========================================================================
    # SCENARIO F: REGRESSION CHECKS
    # =========================================================================
    print("\n[SCENARIO F] Running regression checks on Admin, AI, and Catalog...")
    # Admin Dashboard
    st, adm_dash = make_request(f"{BASE_URL}/admin/dashboard", token=admin_token)
    assert st == 200 and "stats" in adm_dash, f"Admin dashboard failed: {adm_dash}"
    print(f"✓ Admin Dashboard operational: {adm_dash['stats']}")

    # AI Status
    st, ai_st = make_request(f"{BASE_URL}/ai/status")
    assert st == 200 and ai_st.get("status") == "Operational", f"AI service failed: {ai_st}"
    print(f"✓ AI Tutor operational: {ai_st.get('version')}")

    print("\n" + "=" * 70)
    print("ALL MULTI-USER DATA ISOLATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
