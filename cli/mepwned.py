import os
import sys
import time
import threading
import itertools
import subprocess

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CYAN    = "\033[96m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
DIM     = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

BANNER = f"""{CYAN}
  ███╗   ███╗███████╗██████╗ ██╗    ██╗███╗   ██╗███████╗██████╗ 
  ████╗ ████║██╔════╝██╔══██╗██║    ██║████╗  ██║██╔════╝██╔══██╗
  ██╔████╔██║█████╗  ██████╔╝██║ █╗ ██║██╔██╗ ██║█████╗  ██║  ██║
  ██║╚██╔╝██║██╔══╝  ██╔═══╝ ██║███╗██║██║╚██╗██║██╔══╝  ██║  ██║
  ██║ ╚═╝ ██║███████╗██║     ╚███╔███╔╝██║ ╚████║███████╗██████╔╝
  ╚═╝     ╚═╝╚══════╝╚═╝      ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝╚═════╝ 
{RESET}{DIM}
  ╔══════════════════════════════════════════════╗
  ║               {RESET}{CYAN}MEPWNED v1.0 {RESET}{DIM}                  ║
  ║           Enumeration & Credential Suite     ║
  ╚══════════════════════════════════════════════╝
{RESET}"""

TOOLS = [
    {
        "name":  "CROWBAR",
        "desc":  "credential rip via student portal endpoint",
        "path":  os.path.abspath("madcrow.py"),
        "color": CYAN,
        "tag":   "harvest / creds",
    },
    {
        "name":  "REAPER",
        "desc":  "grade header recon & enumeration",
        "path":  os.path.abspath("styx.py"),
        "color": MAGENTA,
        "tag":   "recon  / enum",
    },
    {
        "name":  "NEXUS",
        "desc":  "grade manipulation kill chain (5-step)",
        "path":  os.path.abspath("nexus.py"),
        "color": RED,
        "tag":   "chain  / exploit",
    },
    {
        "name":  "TRASHFIRE",
        "desc":  "unauth mastersheet mass grade dump",
        "path":  os.path.abspath("dumpster.py"),
        "color": YELLOW,
        "tag":   "dump   / unauth",
    },
    {
        "name":  "EXECVEIL",
        "desc":  "formula injection → obfuscated RCE webshell",
        "path":  os.path.abspath("execveil.py"),
        "color": RED,
        "tag":   "rce    / inject",
    },
    {
        "name":  "KILLCHAIN",
        "desc":  "automated trashfire → reaper → nexus sweep",
        "path":  os.path.abspath("workflow.py"),
        "color": GREEN,
        "tag":   "auto   / chain",
    },
    {
        "name":  "VENOM",
        "desc":  "unauth raw SQL exec + full DB table dump",
        "path":  os.path.abspath("sqlpwn.py"),
        "color": RED,
        "tag":   "sqli   / unauth",
    },
    {
        "name":  "SPECTER",
        "desc":  "unauth PII / cred / backup / grade-post ghost",
        "path":  os.path.abspath("ghost.py"),
        "color": DIM,
        "tag":   "ghost  / unauth",
    },
    {
        "name":  "WRAITH",
        "desc":  "SSRF + path traversal .env & file stealer",
        "path":  os.path.abspath("ssrfetch.py"),
        "color": MAGENTA,
        "tag":   "ssrf   / lfi",
    },
    {
        "name":  "LOCKPICK",
        "desc":  "cashier void PIN bruteforce → transaction void",
        "path":  os.path.abspath("pincrack.py"),
        "color": YELLOW,
        "tag":   "brute  / cashier",
    },
    {
        "name":  "SIREN",
        "desc":  "unauth SMS inject / flood any phone number",
        "path":  os.path.abspath("smsbomb.py"),
        "color": CYAN,
        "tag":   "inject / unauth",
    },
    {
        "name":  "KEYHAMMER",
        "desc":  "mass account takeover via password reset sweep",
        "path":  os.path.abspath("passreset.py"),
        "color": RED,
        "tag":   "takeover/ auth",
    },
    {
        "name":  "CODEX",
        "desc":  "tool reference, usage guide & cheat sheet",
        "path":  os.path.abspath("help.py"),
        "color": GREEN,
        "tag":   "docs   / ref",
    },
    {
        "name":  "AUTOSCAN",
        "desc":  "automated security verification (all findings)",
        "path":  os.path.abspath("autoscan.py"),
        "color": GREEN,
        "tag":   "verify / all",
    },
]

_running = False

def _spin_worker(label):
    for c in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
        if not _running:
            break
        print(f"\r  {CYAN}[*]{RESET} {label} {DIM}{c}{RESET}", end="", flush=True)
        time.sleep(0.08)

def check_modules():
    global _running

    # phase 1: decorative init spinner
    _running = True
    t = threading.Thread(target=_spin_worker, args=("Initializing modules",), daemon=True)
    t.start()
    time.sleep(1.8)
    _running = False
    t.join()
    print(f"\r  {GREEN}[+]{RESET} Initializing modules {DIM}— ready.{RESET}         ")

    # phase 2: actual module checks
    print(f"\n  {DIM}Checking module availability...{RESET}\n")
    time.sleep(0.2)

    results = []
    for tool in TOOLS:
        path = tool["path"]
        name = tool["name"]

        if not os.path.exists(path):
            results.append((name, path, "missing", None))
            continue

        result = subprocess.run(
            [sys.executable, "-m", "py_compile", path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "syntax error"
            results.append((name, path, "error", err))
        else:
            results.append((name, path, "ok", None))

    all_ok = True
    for name, path, status, err in results:
        if status == "ok":
            print(f"  {GREEN}[✓]{RESET} {name}  {DIM}{path}{RESET}")
        elif status == "missing":
            print(f"  {RED}[✗]{RESET} {name}  {YELLOW}not found → {path}{RESET}")
            all_ok = False
        elif status == "error":
            print(f"  {RED}[✗]{RESET} {name}  {RED}syntax error:{RESET} {DIM}{err}{RESET}")
            all_ok = False

    if all_ok:
        print(f"\n  {GREEN}[+]{RESET} All modules OK — ready to launch.")
    else:
        print(f"\n  {YELLOW}[!]{RESET} Some modules have issues — they may fail at launch.")

def print_menu():
    print(f"\n  {DIM}┌{'─' * 50}┐{RESET}")
    for i, tool in enumerate(TOOLS, 1):
        pad = 24 - len(tool["name"])
        print(
            f"  {DIM}│{RESET}  {tool['color']}[{i}]{RESET} "
            f"{BOLD}{tool['name']}{RESET}"
            f"{' ' * pad}{DIM}{tool['desc']}{RESET}"
        )
    print(f"  {DIM}│{RESET}  {RED}[0]{RESET}  Exit")
    print(f"  {DIM}└{'─' * 50}┘{RESET}\n")

def launch(tool):
    path = tool["path"]
    if not os.path.exists(path):
        print(f"\n  {RED}[!]{RESET} Script not found: {YELLOW}{path}{RESET}\n")
        return
    print(f"\n  {GREEN}[>]{RESET} Spawning {BOLD}{tool['name']}{RESET} {DIM}({path}){RESET}\n")
    time.sleep(0.3)
    try:
        subprocess.run([sys.executable, path])
    except KeyboardInterrupt:
        pass
    print(f"\n  {DIM}[*] Process exited — back in MePwned.{RESET}")
    input(f"  {DIM}Press Enter to continue...{RESET} ")

os.system("cls" if os.name == "nt" else "clear")
print(BANNER)
check_modules()
print()

while True:
    print_menu()
    try:
        choice = input(
            f"  {DIM}┌─[{RESET}{CYAN}mepwned{RESET}{DIM}@{RESET}{YELLOW}mwpwned{RESET}{DIM}]─[~]{RESET}\n"
            f"  {DIM}└──╼{RESET} {GREEN}${RESET} "
        ).strip()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}[!]{RESET} Caught interrupt — exiting.\n")
        sys.exit(0)

    if choice == "0":
        print(f"\n  {YELLOW}[!]{RESET} Exiting MePwned.\n")
        sys.exit(0)
    elif choice.isdigit() and 1 <= int(choice) <= len(TOOLS):
        os.system("cls" if os.name == "nt" else "clear")
        print(BANNER)
        launch(TOOLS[int(choice) - 1])
        os.system("cls" if os.name == "nt" else "clear")
        print(BANNER)
    else:
        print(f"\n  {RED}[!]{RESET} Invalid selection — try again.\n")
