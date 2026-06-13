import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CYAN    = "\033[96m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
DIM     = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

# ── layout helpers ────────────────────────────────────────────────────────────

W = 72  # inner box width

def box_top(color=DIM):
    print(f"  {color}╔{'═' * W}╗{RESET}")

def box_row(text="", color=DIM, pad=True):
    visible = _strip(text)
    space   = W - visible
    if pad:
        print(f"  {color}║{RESET} {text}{' ' * (space - 1)}{color}║{RESET}")
    else:
        print(f"  {color}║{RESET}{text}{color}║{RESET}")

def box_div(color=DIM):
    print(f"  {color}╠{'═' * W}╣{RESET}")

def box_mid_div(color=DIM):
    print(f"  {color}╟{'─' * W}╢{RESET}")

def box_bot(color=DIM):
    print(f"  {color}╚{'═' * W}╝{RESET}")

def _strip(s):
    """Length of string ignoring ANSI escape codes."""
    import re
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

def label(tag, text, tc=CYAN, vc=RESET):
    return f"{DIM}{tc}{BOLD}{tag}{RESET}{DIM}  {RESET}{vc}{text}{RESET}"

def field(name, val, nc=DIM, vc=YELLOW):
    return f"  {nc}{name:<14}{RESET}{vc}{val}{RESET}"

def indent(text, color=RESET):
    return f"  {color}{text}{RESET}"

# ── banner ────────────────────────────────────────────────────────────────────

print(f"""
{CYAN}  ██╗  ██╗███████╗██╗     ██████╗      ██████╗ ██╗
  ██║  ██║██╔════╝██║     ██╔══██╗    ██╔════╝ ██║
  ███████║█████╗  ██║     ██████╔╝    ██║  ███╗██║
  ██╔══██║██╔══╝  ██║     ██╔═══╝     ██║   ██║╚═╝
  ██║  ██║███████╗███████╗██║         ╚██████╔╝██╗
  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝          ╚═════╝ ╚═╝{RESET}
{DIM}  ╔══════════════════════════════════════════════════╗
  ║   {RESET}{CYAN}PHANTOMIDX v1.0 — Tool Reference & Usage Guide{RESET}{DIM}   ║
  ╚══════════════════════════════════════════════════╝{RESET}
""")

# ══════════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

box_top()
box_row(f"{BOLD}{CYAN}  SUITE OVERVIEW{RESET}")
box_div()
box_row()
box_row(indent(f"Target   {DIM}→{RESET}  {YELLOW}http://es_ldcu.dev{RESET}  {DIM}(school grading portal){RESET}"))
box_row(indent(f"Auth     {DIM}→{RESET}  {DIM}most endpoints require no session (unauthenticated){RESET}"))
box_row(indent(f"Launcher {DIM}→{RESET}  {CYAN}python mepwned.py{RESET}  {DIM}runs any tool from the menu{RESET}"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"  {CYAN}1{RESET}  {BOLD}MadCrow{RESET}   {DIM}·{RESET}  harvest student & parent credentials"))
box_row(indent(f"  {MAGENTA}2{RESET}  {BOLD}Styx{RESET}      {DIM}·{RESET}  enumerate grade headers across all combos"))
box_row(indent(f"  {RED}3{RESET}  {BOLD}Nexus{RESET}     {DIM}·{RESET}  full grade manipulation chain (5 steps)"))
box_row(indent(f"  {YELLOW}4{RESET}  {BOLD}Dumpster{RESET}  {DIM}·{RESET}  dump all student grades (unauthenticated)"))
box_row(indent(f"  {GREEN}5{RESET}  {BOLD}Help{RESET}      {DIM}·{RESET}  this screen"))
box_row()
box_bot()

print()

# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 1 — MADCROW
# ══════════════════════════════════════════════════════════════════════════════

box_top(CYAN)
box_row(f"{BOLD}{CYAN}  [1]  MADCROW HARVESTER{RESET}  {DIM}· credential dump via student portal{RESET}", CYAN)
box_div(CYAN)
box_row()
box_row(indent(f"{BOLD}What it does{RESET}"))
box_row(indent(f"{DIM}Iterates every (section × level) pair (sec 1–99, lvl 1–19) and calls{RESET}"))
box_row(indent(f"{DIM}/teacher/student/credential/list — returns plaintext student &{RESET}"))
box_row(indent(f"{DIM}parent credentials (username, password, email) for each record.{RESET}"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Inputs{RESET}"))
box_row(field("BASE_URL",        "http://es_ldcu.dev"))
box_row(field("SESSION_COOKIE",  "laravel_session value  (student account)"))
box_row(field("XSRF_COOKIE",     "XSRF-TOKEN cookie value"))
box_row(field("SY_ID",           "school year ID  (usually 1)"))
box_row(field("MAX_CONCURRENT",  "async request limit  (default 30)"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Output{RESET}"))
box_row(indent(f"{DIM}Saves to {RESET}{YELLOW}credentials.json{RESET}{DIM} — array of objects with fields:{RESET}"))
box_row(indent(f"{DIM}  studid · username · password · parent_username · parent_password{RESET}"))
box_row()
box_row(indent(f"{BOLD}Run{RESET}"))
box_row(indent(f"{CYAN}python cli/madcrow.py{RESET}"))
box_row()
box_bot(CYAN)

print()

# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 2 — STYX
# ══════════════════════════════════════════════════════════════════════════════

box_top(MAGENTA)
box_row(f"{BOLD}{MAGENTA}  [2]  STYX{RESET}  {DIM}· grade header enumerator (unauthenticated){RESET}", MAGENTA)
box_div(MAGENTA)
box_row()
box_row(indent(f"{BOLD}What it does{RESET}"))
box_row(indent(f"{DIM}Brute-forces /get/grade/header across all combinations of{RESET}"))
box_row(indent(f"{DIM}section × level × subject × quarter.  No session required.{RESET}"))
box_row(indent(f"{DIM}Reveals header IDs needed by Nexus.{RESET}"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Inputs{RESET}"))
box_row(field("BASE_URL",     "http://es_ldcu.dev"))
box_row(field("SY_ID",        "school year ID"))
box_row(field("SID_RANGE",    "section ID range   e.g. 1-100"))
box_row(field("LID_RANGE",    "level ID range     e.g. 1-20"))
box_row(field("SUBID_RANGE",  "subject ID range   e.g. 1-30"))
box_row(field("QUARTER",      "quarter number     1-4"))
box_row(field("MAX_CONC",     "async concurrency  (default 40)"))
box_row(field("DEBUG",        "y/N — print full URL + response per request"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Output{RESET}"))
box_row(indent(f"{DIM}Saves to {RESET}{YELLOW}headers.json{RESET}{DIM} — array of header objects with:{RESET}"))
box_row(indent(f"{DIM}  id · syid · sectionid · subjid · quarter · status · submitted{RESET}"))
box_row()
box_row(indent(f"{BOLD}Run{RESET}"))
box_row(indent(f"{MAGENTA}python cli/styx.py{RESET}"))
box_row()
box_bot(MAGENTA)

print()

# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 3 — NEXUS
# ══════════════════════════════════════════════════════════════════════════════

box_top(RED)
box_row(f"{BOLD}{RED}  [3]  NEXUS{RESET}  {DIM}· grade manipulation chain — 5-step exploit{RESET}", RED)
box_div(RED)
box_row()
box_row(indent(f"{BOLD}What it does{RESET}"))
box_row(indent(f"{DIM}Executes a sequential attack chain against the grading portal:{RESET}"))
box_row()
box_row(indent(f"  {RED}①{RESET}  GET /get/grade/header          {DIM}→ retrieve header_id{RESET}"))
box_row(indent(f"  {RED}②{RESET}  GET /grades/report/mastersheet {DIM}→ find target student, get detail_id{RESET}"))
box_row(indent(f"  {RED}③{RESET}  GET /gradesdetail/update       {DIM}→ inflate grade to target value{RESET}"))
box_row(indent(f"  {RED}④{RESET}  GET /gradesheader/update       {DIM}→ force header status = 3 (approved){RESET}"))
box_row(indent(f"  {RED}⑤{RESET}  GET /posting/grade/.../approve {DIM}→ trigger workflow approval{RESET}"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Inputs{RESET}"))
box_row(field("BASE_URL",           "http://es_ldcu.dev"))
box_row(field("TARGET_SY",          "school year ID"))
box_row(field("TARGET_SECTION",     "section ID of the target student"))
box_row(field("TARGET_LEVEL",       "grade level ID"))
box_row(field("TARGET_SUBJ",        "subject ID"))
box_row(field("TARGET_QUARTER",     "quarter  (1–4)"))
box_row(field("TARGET_STUDID",      "student ID to manipulate"))
box_row(field("TARGET_GRADE",       "grade value to set  (default 100)"))
box_row(field("STUDENT_SESSION",    "laravel_session  (any student account)"))
box_row(field("NONDEFAULT_SESSION", "laravel_session  (non-default password account)"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Tip{RESET}"))
box_row(indent(f"{DIM}Run Styx first to discover valid section/level/subject/header combos.{RESET}"))
box_row(indent(f"{DIM}Run Dumpster to find TARGET_STUDID for the target student.{RESET}"))
box_row()
box_row(indent(f"{BOLD}Run{RESET}"))
box_row(indent(f"{RED}python cli/nexus.py{RESET}"))
box_row()
box_bot(RED)

print()

# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 4 — DUMPSTER
# ══════════════════════════════════════════════════════════════════════════════

box_top(YELLOW)
box_row(f"{BOLD}{YELLOW}  [4]  DUMPSTER{RESET}  {DIM}· full grade dump — unauthenticated{RESET}", YELLOW)
box_div(YELLOW)
box_row()
box_row(indent(f"{BOLD}What it does{RESET}"))
box_row(indent(f"{DIM}Brute-forces /grades/report/mastersheet across all section IDs.{RESET}"))
box_row(indent(f"{DIM}No session required.  Returns full student records including{RESET}"))
box_row(indent(f"{DIM}lastname, firstname, and grades per subject.{RESET}"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Inputs{RESET}"))
box_row(field("BASE_URL",   "http://es_ldcu.dev"))
box_row(field("SY_ID",      "school year ID  (default 1)"))
box_row(field("LEVEL_ID",   "grade level ID  (default 3)"))
box_row(field("QUARTER",    "quarter  (default 1)"))
box_row(field("SID_RANGE",  "section ID range  e.g. 1-500"))
box_row(field("MAX_CONC",   "async concurrency  (default 50)"))
box_row(field("OUT_FILE",   "output filename  (default dump.json)"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{BOLD}Output{RESET}"))
box_row(indent(f"{DIM}Saves to {RESET}{YELLOW}dump.json{RESET}{DIM} — array of objects per section:{RESET}"))
box_row(indent(f"{DIM}  section_id · students[ id · lastname · firstname · grade... ]{RESET}"))
box_row()
box_row(indent(f"{BOLD}Run{RESET}"))
box_row(indent(f"{YELLOW}python cli/dumpster.py{RESET}"))
box_row()
box_bot(YELLOW)

print()

# ══════════════════════════════════════════════════════════════════════════════
#  TYPICAL WORKFLOW
# ══════════════════════════════════════════════════════════════════════════════

box_top(GREEN)
box_row(f"{BOLD}{GREEN}  RECOMMENDED WORKFLOW{RESET}", GREEN)
box_div(GREEN)
box_row()
box_row(indent(f"{DIM}Step 1{RESET}  {GREEN}Dumpster{RESET}  {DIM}→{RESET}  enumerate all sections, find target student ID"))
box_row(indent(f"{DIM}Step 2{RESET}  {MAGENTA}Styx{RESET}      {DIM}→{RESET}  find valid header (section/level/subject/quarter)"))
box_row(indent(f"{DIM}Step 3{RESET}  {CYAN}MadCrow{RESET}   {DIM}→{RESET}  harvest a student session cookie if needed"))
box_row(indent(f"{DIM}Step 4{RESET}  {RED}Nexus{RESET}     {DIM}→{RESET}  execute the manipulation chain with gathered data"))
box_row()
box_row(indent(f"{DIM}{'─' * 66}{RESET}"))
box_row()
box_row(indent(f"{DIM}All tools support {RESET}{YELLOW}Ctrl+C{RESET}{DIM} — partial results are saved before exit.{RESET}"))
box_row(indent(f"{DIM}Launch everything from {RESET}{CYAN}python mepwned.py{RESET}"))
box_row()
box_bot(GREEN)

print()
