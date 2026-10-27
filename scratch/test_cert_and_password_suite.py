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

def run_tests():
    ts = int(time.time())
    print("=" * 60)
    print("AI-LMS COMPREHENSIVE CERTIFICATE & PASSWORD ACCEPTANCE SUITE")
    print("=" * 60)

    # -------------------------------------------------------------
    # TASK 2: PASSWORD VALIDATION TESTS
    # -------------------------------------------------------------
    print("\n--- TASK 2: PASSWORD COMPLEXITY VALIDATION TESTS ---")

    # 1. Reject length < 8
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "Short Pass User",
        "email": f"short_{ts}@test.com",
        "password": "Pa@1"
    })
    print(f"Test 1: 'Pa@1' (too short) -> Status: {status}, Msg: {res.get('message')}")
    assert status == 400, f"Expected 400 for short password, got {status}"
    assert "8 characters" in res.get("message", ""), f"Unexpected error message: {res}"

    # 2. Reject no uppercase
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "No Upper User",
        "email": f"noupper_{ts}@test.com",
        "password": "password@123"
    })
    print(f"Test 2: 'password@123' (no uppercase) -> Status: {status}, Msg: {res.get('message')}")
    assert status == 400, f"Expected 400 for no uppercase, got {status}"
    assert "uppercase" in res.get("message", "").lower(), f"Unexpected error message: {res}"

    # 3. Reject no digit
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "No Digit User",
        "email": f"nodigit_{ts}@test.com",
        "password": "Password!"
    })
    print(f"Test 3: 'Password!' (no digit) -> Status: {status}, Msg: {res.get('message')}")
    assert status == 400, f"Expected 400 for no digit, got {status}"
    assert "digit" in res.get("message", "").lower(), f"Unexpected error message: {res}"

    # 4. Reject no special char
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "No Special User",
        "email": f"nospec_{ts}@test.com",
        "password": "Password123"
    })
    print(f"Test 4: 'Password123' (no special char) -> Status: {status}, Msg: {res.get('message')}")
    assert status == 400, f"Expected 400 for no special char, got {status}"
    assert "special character" in res.get("message", "").lower(), f"Unexpected error message: {res}"

    # 5. Accept valid password: Sushant@123
    student_a_email = f"student_a_{ts}@learnova.ai"
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "Student A",
        "email": student_a_email,
        "password": "Sushant@123"
    })
    print(f"Test 5: 'Sushant@123' (valid) -> Status: {status}, Msg: {res.get('message')}")
    assert status == 200, f"Expected 200 for valid password Sushant@123, got {status}: {res}"
    student_a_id = res.get("userId")

    # 6. Accept valid password: Password1!
    student_b_email = f"student_b_{ts}@learnova.ai"
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "name": "Student B",
        "email": student_b_email,
        "password": "Password1!"
    })
    print(f"Test 6: 'Password1!' (valid) -> Status: {status}, Msg: {res.get('message')}")
    assert status == 200, f"Expected 200 for valid password Password1!, got {status}: {res}"
    student_b_id = res.get("userId")

    # 7. Check Existing Users Login Compatibility
    print("\n--- CHECKING EXISTING USERS LOGIN COMPATIBILITY ---")
    status, res = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": "student@learnova.ai",
        "password": "Student@123"
    })
    assert status == 200, f"Existing student login failed: {res}"
    print("✓ Existing student (student@learnova.ai) logged in successfully.")

    status, res = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": "admin@learnova.ai",
        "password": "Admin@123"
    })
    assert status == 200, f"Admin login failed: {res}"
    admin_token = res["token"]
    print("✓ Admin (admin@learnova.ai) logged in successfully.")

    # -------------------------------------------------------------
    # TASK 1: CERTIFICATE VISIBILITY & OWNERSHIP TESTS
    # -------------------------------------------------------------
    print("\n--- TASK 1: CERTIFICATE OWNERSHIP AND VISIBILITY TESTS ---")

    # Log in Student A
    status, res = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": student_a_email,
        "password": "Sushant@123"
    })
    assert status == 200, f"Student A login failed: {res}"
    token_a = res["token"]

    # Log in Student B
    status, res = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": student_b_email,
        "password": "Password1!"
    })
    assert status == 200, f"Student B login failed: {res}"
    token_b = res["token"]

    # Rule 1: A newly registered student must have zero certificates
    status, certs_a = make_request(f"{BASE_URL}/certificates/my", method="GET", token=token_a)
    print(f"Rule 1 Check - Student A initial certificates: Count = {len(certs_a)}")
    assert status == 200, f"Failed to get certificates for Student A: {certs_a}"
    assert len(certs_a) == 0, f"Expected 0 certificates for new Student A, found {len(certs_a)}"

    status, certs_b = make_request(f"{BASE_URL}/certificates/my", method="GET", token=token_b)
    print(f"Rule 1 Check - Student B initial certificates: Count = {len(certs_b)}")
    assert status == 200, f"Failed to get certificates for Student B: {certs_b}"
    assert len(certs_b) == 0, f"Expected 0 certificates for new Student B, found {len(certs_b)}"

    # Get a course to test completion
    status, courses = make_request(f"{BASE_URL}/courses", method="GET")
    assert status == 200 and len(courses) > 0, "No courses found."
    test_course = courses[0]
    course_id = test_course["id"]
    course_title = test_course["title"]
    print(f"Using Course: '{course_title}' (ID: {course_id})")

    # Rule 2: Premature claim without completing course must be rejected
    status, claim_res = make_request(f"{BASE_URL}/certificates/claim/{course_id}", method="POST", token=token_a)
    print(f"Rule 2 Check - Student A premature certificate claim status: {status}, Msg: {claim_res.get('message')}")
    assert status in [400, 404], f"Expected rejection for premature certificate claim, got {status}"

    # Enroll Student A in the course
    status, enroll_res = make_request(f"{BASE_URL}/courses/{course_id}/enroll", method="POST", token=token_a)
    assert status == 200, f"Enrollment failed for Student A: {enroll_res}"
    print("✓ Student A enrolled in course.")

    # Student A completes all lessons in the course
    print("Completing all course lessons for Student A to legitimately earn certificate...")
    chapters = test_course.get("chapters", [])
    total_completed = 0
    for ch in chapters:
        for lesson in ch.get("lessons", []):
            les_id = lesson["id"]
            # 1. Send video progress (>90%)
            status, vp_res = make_request(
                f"{BASE_URL}/courses/{course_id}/lessons/{les_id}/video-progress",
                method="POST",
                data={
                    "watchedSeconds": 950,
                    "videoDuration": 1000,
                    "watchedPercentage": 95,
                    "lastPositionSeconds": 950
                },
                token=token_a
            )
            assert status == 200, f"Video progress failed for {les_id}: {vp_res}"

            # 2. Complete lesson
            status, comp_res = make_request(
                f"{BASE_URL}/courses/{course_id}/lessons/{les_id}/complete",
                method="POST",
                token=token_a
            )
            assert status == 200, f"Complete lesson failed for {les_id}: {comp_res}"
            total_completed += 1

    print(f"✓ All {total_completed} lessons completed for Student A.")

    # Rule 3: Student A now has 1 earned certificate
    status, certs_a_earned = make_request(f"{BASE_URL}/certificates/my", method="GET", token=token_a)
    assert status == 200, f"Failed to retrieve earned certificates: {certs_a_earned}"
    assert len(certs_a_earned) == 1, f"Expected 1 certificate for Student A, got {len(certs_a_earned)}"
    cert_a = certs_a_earned[0]
    cert_a_number = cert_a["certificateNumber"]
    cert_a_id = cert_a["id"]
    print(f"✓ Student A earned certificate: {cert_a_number} (ID: {cert_a_id})")

    # Rule 4: Relogging in preserves certificate visibility for Student A
    status, relogin = make_request(f"{BASE_URL}/auth/login", method="POST", data={
        "email": student_a_email,
        "password": "Sushant@123"
    })
    assert status == 200, "Relogin failed"
    token_a_new = relogin["token"]
    status, certs_a_relogin = make_request(f"{BASE_URL}/certificates/my", method="GET", token=token_a_new)
    assert len(certs_a_relogin) == 1, "Certificate missing after relogin!"
    print("✓ Student A certificate is persistent across sessions and logins.")

    # Rule 5: Student B still sees zero certificates!
    status, certs_b_check = make_request(f"{BASE_URL}/certificates/my", method="GET", token=token_b)
    assert len(certs_b_check) == 0, f"CRITICAL LEAK: Student B can see {len(certs_b_check)} certificates!"
    print("✓ Student B still sees 0 certificates (No cross-user certificate leakage).")

    # Rule 6: Student B cannot access Student A's certificate directly via ID (Backend Ownership Enforcement)
    status, direct_access = make_request(f"{BASE_URL}/certificates/{cert_a_id}", method="GET", token=token_b)
    print(f"Rule 6 Check - Student B direct access to Student A's cert ID: Status = {status}")
    assert status == 403, f"Expected 403 Forbidden for Student B accessing Student A's cert, got {status}: {direct_access}"
    print("✓ Backend strictly enforces ownership: Student B direct retrieval returned 403 Forbidden.")

    status, direct_access_num = make_request(f"{BASE_URL}/certificates/{cert_a_number}", method="GET", token=token_b)
    assert status == 403, f"Expected 403 Forbidden for Student B accessing cert by number, got {status}"
    print("✓ Backend ownership verified for both Mongo ID and CertificateNumber queries.")

    # Rule 7: Public Certificate Verification works without leaking private student credentials
    status, verify_res = make_request(f"{BASE_URL}/certificates/verify/{cert_a_number}", method="GET")
    print(f"Rule 7 Check - Public certificate verification status: {status}")
    assert status == 200, f"Verification failed: {verify_res}"
    assert verify_res.get("verified") == True, "Verification failed"
    assert verify_res.get("studentName") == "Student A"
    assert verify_res.get("courseTitle") == course_title
    assert "password" not in str(verify_res).lower()
    assert "passwordhash" not in str(verify_res).lower()
    print(f"✓ Public verification succeeded: Verified credential for {verify_res.get('studentName')} on '{verify_res.get('courseTitle')}'.")

    # Rule 8: Admin can view all certificates
    status, admin_certs = make_request(f"{BASE_URL}/certificates/admin", method="GET", token=admin_token)
    assert status == 200, f"Admin certificates retrieval failed: {admin_certs}"
    assert any(c["certificateNumber"] == cert_a_number for c in admin_certs), "Admin could not find Student A's certificate."
    print("✓ Admin oversight verified: Admin can retrieve official certificates.")

    print("\n" + "=" * 60)
    print("ALL ACCEPTANCE TESTS PASSED SUCCESSFULLY! (100% VERIFIED)")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
