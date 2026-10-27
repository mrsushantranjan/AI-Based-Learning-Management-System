import urllib.request
import urllib.error
import json

base_url = "http://localhost:5291/api"

# Login
req = urllib.request.Request(f"{base_url}/auth/login", data=json.dumps({"email": "student@learnova.ai", "password": "Student@123"}).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    token = json.loads(r.read().decode())["token"]

req2 = urllib.request.Request(f"{base_url}/courses")
with urllib.request.urlopen(req2) as r2:
    courses = json.loads(r2.read().decode())

target_course = [c for c in courses if "microprocessor" in c["title"].lower()][0]
cid = target_course["id"]
title = target_course["title"]
print(f"Testing on course: {title} (ID: {cid})")

# Enroll
req_enroll = urllib.request.Request(f"{base_url}/courses/{cid}/enroll", data=b"", headers={"Authorization": f"Bearer {token}"})
urllib.request.urlopen(req_enroll)

# Check Initial state
req_prog = urllib.request.Request(f"{base_url}/courses/{cid}/progress", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req_prog) as rp:
    prog = json.loads(rp.read().decode())

l1_id = target_course["chapters"][0]["lessons"][0]["id"]
l2_id = target_course["chapters"][0]["lessons"][1]["id"]

assert l1_id in prog["unlockedLessonIds"], "L1 unlocked"
assert l2_id not in prog["unlockedLessonIds"], "L2 locked"
print("✓ Initial state: Lesson 1 unlocked, Lesson 2 locked")

# Test premature complete
try:
    req_comp_fail = urllib.request.Request(f"{base_url}/courses/{cid}/lessons/{l1_id}/complete", data=b"{}", headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    urllib.request.urlopen(req_comp_fail)
    print("FAILED: completion should have been rejected!")
except urllib.error.HTTPError as e:
    print(f"✓ Premature completion properly rejected by backend with HTTP {e.code}: {e.read().decode()}")

# Send 92% video watch progress
req_vprog = urllib.request.Request(f"{base_url}/courses/{cid}/lessons/{l1_id}/video-progress", data=json.dumps({
    "watchedSeconds": 920,
    "videoDuration": 1000,
    "watchedPercentage": 92,
    "lastPositionSeconds": 920
}).encode("utf-8"), headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req_vprog) as rvp:
    vp_res = json.loads(rvp.read().decode())
    assert vp_res["videoRequirementCompleted"] == True
    print("✓ Video progress saved: requirement completed = True")

# Complete lesson 1 legitimately
req_comp_ok = urllib.request.Request(f"{base_url}/courses/{cid}/lessons/{l1_id}/complete", data=b"{}", headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req_comp_ok) as rco:
    comp_ok = json.loads(rco.read().decode())
    assert comp_ok["success"] == True
    print("✓ Lesson 1 completed successfully!")

with urllib.request.urlopen(req_prog) as rp2:
    prog2 = json.loads(rp2.read().decode())
    assert l2_id in prog2["unlockedLessonIds"]
    print("✓ Lesson 2 unlocked successfully after 90% watch and verified completion!")

print("\nSUCCESS: All video playback, watch threshold, and sequential progression tests passed!")
