"""
AUTOSCAN — Automated Security Verification Scanner
═══════════════════════════════════════════════════
Non-destructive endpoint verification mapped 1:1 to the Unified POC document.
Determines: VULNERABLE / PATCHED / UNREACHABLE for each finding.

Usage:
    python autoscan.py                                 (interactive)
    python autoscan.py --url http://target --quiet     (CI mode)
    python autoscan.py --url http://target --session <cookie> --json report.json
"""

import sys
import os
import json
import time
import asyncio
import re
import aiohttp
import argparse
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

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
  ┌─────────────────────────────────────────────────────────┐
  │  {BOLD}AUTOSCAN{RESET}{CYAN}  — Security Verification Engine              │
  │  Non-destructive · Maps to Unified Security Report      │
  │  64 checks · 11 modules · Parallel execution            │
  └─────────────────────────────────────────────────────────┘
{RESET}"""


@dataclass
class TestResult:
    finding_id: str
    module: str
    severity: str
    title: str
    status: str
    detail: str = ""
    http_status: Optional[int] = None
    response_time_ms: Optional[float] = None


@dataclass
class ScanReport:
    target_url: str
    scan_date: str
    scan_duration_sec: float = 0.0
    results: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# ── Response Analysis ─────────────────────────────────────────────────────────

def _is_login_page(text):
    lower = text[:2000].lower()
    return ('name="password"' in lower or
            'type="password"' in lower or
            ('<form' in lower and 'login' in lower))


def _check_json_data(resp_text, status_code):
    if status_code == 200:
        try:
            data = json.loads(resp_text)
            if isinstance(data, list) and len(data) > 0:
                return "VULNERABLE", f"Returns {len(data)} records"
            if isinstance(data, dict):
                if data.get("data") and isinstance(data["data"], list) and len(data["data"]) > 0:
                    return "VULNERABLE", f"Returns {len(data['data'])} records"
                if data.get("success") or data.get("status"):
                    return "VULNERABLE", "Returns success response"
                if len(data) > 2:
                    return "VULNERABLE", f"Returns object ({len(data)} keys)"
        except (json.JSONDecodeError, TypeError):
            if not _is_login_page(resp_text):
                return "VULNERABLE", "Non-JSON 200 (endpoint accessible)"
    if status_code in (401, 403):
        return "PATCHED", f"HTTP {status_code}"
    if status_code == 302:
        return "PATCHED", "Redirects"
    if status_code == 404:
        return "PATCHED", "Route removed"
    if status_code == 500:
        return "ERROR", "Server error"
    return "PATCHED", f"HTTP {status_code}"


def _check_unauth(resp_text, status_code):
    if status_code == 200:
        if _is_login_page(resp_text):
            return "PATCHED", "Returns login page"
        return "VULNERABLE", "Accessible without auth"
    if status_code in (401, 403):
        return "PATCHED", f"HTTP {status_code}"
    if status_code == 302:
        return "PATCHED", "Redirects to login"
    if status_code == 404:
        return "PATCHED", "Route removed"
    if status_code == 405:
        return "PATCHED", "Method not allowed"
    if status_code == 500:
        return "ERROR", "Server error (route exists)"
    return "PATCHED", f"HTTP {status_code}"


def _check_password_field(resp_text, status_code):
    if status_code == 200:
        if "passwordstr" in resp_text:
            return "VULNERABLE", "Contains plaintext passwords"
        if _is_login_page(resp_text):
            return "PATCHED", "Returns login page"
        return "PATCHED", "200 but no password field"
    if status_code in (401, 403, 302):
        return "PATCHED", f"HTTP {status_code}"
    if status_code == 404:
        return "PATCHED", "Route removed"
    return "PATCHED", f"HTTP {status_code}"


def _check_action(resp_text, status_code):
    if status_code == 200:
        if _is_login_page(resp_text):
            return "PATCHED", "Returns login page"
        try:
            data = json.loads(resp_text)
            if isinstance(data, list) and data:
                return "VULNERABLE", "Action endpoint reachable"
            if isinstance(data, dict) and (data.get("status") or data.get("success") or data.get("message")):
                return "VULNERABLE", "Action responds"
        except:
            pass
        return "VULNERABLE", "HTTP 200 — endpoint accessible"
    if status_code in (401, 403):
        return "PATCHED", f"HTTP {status_code}"
    if status_code == 302:
        return "PATCHED", "Redirects to login"
    if status_code == 404:
        return "PATCHED", "Route removed"
    if status_code == 422:
        return "VULNERABLE", "422 — reachable (validation error)"
    if status_code == 500:
        return "ERROR", "500 — route exists"
    return "PATCHED", f"HTTP {status_code}"


def _check_grade(resp_text, status_code):
    if status_code == 200:
        if _is_login_page(resp_text):
            return "PATCHED", "Returns login page"
        return "VULNERABLE", "Grade endpoint accessible"
    if status_code in (401, 403):
        return "PATCHED", f"HTTP {status_code}"
    if status_code == 302:
        return "PATCHED", "Redirects to login"
    if status_code == 404:
        return "PATCHED", "Route removed"
    if status_code == 500:
        return "ERROR", "500 — crashes"
    return "PATCHED", f"HTTP {status_code}"


# ── Test Registry ─────────────────────────────────────────────────────────────

TESTS = [
    # ═══ SuperAdmin (SA-01 → SA-06) ═══
    {"id": "SA-01a", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "SQL exec — synchornization/process/updatelogs",
     "method": "GET", "path": "/synchornization/process/updatelogs",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "SA-01b", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "SQL exec — querylogsToCloud",
     "method": "GET", "path": "/querylogsToCloud",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "SA-01c", "module": "SuperAdmin", "severity": "HIGH",
     "title": "SQL exfil readback — cloudGetSyncSetup",
     "method": "GET", "path": "/cloudGetSyncSetup",
     "params": {}, "needs_auth": False, "check": _check_json_data},
    {"id": "SA-02a", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "DB dump — cloudNewData/users/0",
     "method": "GET", "path": "/cloudNewData/users/0",
     "params": {}, "needs_auth": False, "check": _check_json_data},
    {"id": "SA-02b", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "DB schema — getTableFields/users",
     "method": "GET", "path": "/getTableFields/users",
     "params": {}, "needs_auth": False, "check": _check_json_data},
    {"id": "SA-02c", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "DB write — insertdatatotable",
     "method": "GET", "path": "/insertdatatotable",
     "params": {"table": "syncsetup"}, "needs_auth": False, "check": _check_unauth},
    {"id": "SA-02d", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "DB write — updatetargettable",
     "method": "GET", "path": "/updatetargettable",
     "params": {"table": "syncsetup"}, "needs_auth": False, "check": _check_unauth},
    {"id": "SA-02e", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "DB delete — deletetargettable",
     "method": "GET", "path": "/deletetargettable",
     "params": {"table": "syncsetup"}, "needs_auth": False, "check": _check_unauth},
    {"id": "SA-03", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "SSRF + LFI — storeImage",
     "method": "GET", "path": "/storeImage",
     "params": {"imagepath": "http://127.0.0.1:1", "tablename": "test"},
     "needs_auth": False, "check": _check_unauth},
    {"id": "SA-05a", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "Credential list — student/credentials/list",
     "method": "GET", "path": "/student/credentials/list",
     "params": {}, "needs_auth": False, "check": _check_json_data},
    {"id": "SA-05b", "module": "SuperAdmin", "severity": "CRITICAL",
     "title": "Contact dump — student/contactnumber/list",
     "method": "GET", "path": "/student/contactnumber/list",
     "params": {}, "needs_auth": False, "check": _check_json_data},
    {"id": "SA-06", "module": "SuperAdmin", "severity": "HIGH",
     "title": "DB backup trigger — /backupdb",
     "method": "GET", "path": "/backupdb",
     "params": {}, "needs_auth": False, "check": _check_unauth},

    # ═══ Teacher (T-01 → T-08) ═══
    {"id": "T-01", "module": "Teacher", "severity": "CRITICAL",
     "title": "Grade detail modification (any session)",
     "method": "GET", "path": "/gradesdetail/update",
     "params": {}, "needs_auth": True, "check": _check_grade},
    {"id": "T-02", "module": "Teacher", "severity": "CRITICAL",
     "title": "Grade header status bypass (bulk approve)",
     "method": "GET", "path": "/gradesheader/update",
     "params": {}, "needs_auth": True, "check": _check_grade},
    {"id": "T-03", "module": "Teacher", "severity": "HIGH",
     "title": "Grade approval without teacher role",
     "method": "GET", "path": "/posting/grade/subject/approve",
     "params": {}, "needs_auth": True, "check": _check_grade},
    {"id": "T-04", "module": "Teacher", "severity": "HIGH",
     "title": "Final grade save without teacher auth",
     "method": "GET", "path": "/teacher/finalgrades/savegrades",
     "params": {}, "needs_auth": True, "check": _check_grade},
    {"id": "T-05", "module": "Teacher", "severity": "HIGH",
     "title": "Unauth grade master sheet dump",
     "method": "GET", "path": "/grades/report/mastersheet",
     "params": {"syid": "1", "sectionid": "1", "levelid": "1", "quarter": "1"},
     "needs_auth": False, "check": _check_json_data},
    {"id": "T-06", "module": "Teacher", "severity": "HIGH",
     "title": "Unauth deportment status update",
     "method": "GET", "path": "/posting/grade/update-grade-status",
     "params": {}, "needs_auth": False, "check": _check_grade},
    {"id": "T-07", "module": "Teacher", "severity": "MEDIUM",
     "title": "Unauth grade header enumeration",
     "method": "GET", "path": "/get/grade/header",
     "params": {"syid": "1", "gradelevelid": "1", "subjectid": "1", "quarter": "1", "sectionid": "1"},
     "needs_auth": False, "check": _check_json_data},
    {"id": "T-08", "module": "Teacher", "severity": "HIGH",
     "title": "Cross-teacher attendance manipulation",
     "method": "GET", "path": "/classattendance/submit",
     "params": {}, "needs_auth": True, "check": _check_grade},

    # ═══ Finance V2 (FV2-01 → FV2-03) ═══
    {"id": "FV2-01", "module": "Finance V2", "severity": "CRITICAL",
     "title": "Plaintext PIN via cloudNewData/chrng_pin",
     "method": "GET", "path": "/cloudNewData/chrng_pin/0",
     "params": {}, "needs_auth": False, "check": _check_json_data},
    {"id": "FV2-02", "module": "Finance V2", "severity": "CRITICAL",
     "title": "Void bypass — no backend PIN check",
     "method": "GET", "path": "/view-account/adjustment",
     "params": {}, "needs_auth": True, "check": _check_unauth},
    {"id": "FV2-03", "module": "Finance V2", "severity": "CRITICAL",
     "title": "PIN brute force — no rate limit",
     "method": "POST", "path": "/view-account/verify-void-pin",
     "params": {}, "body": {"pin": "0000"}, "needs_auth": True, "check": _check_action},

    # ═══ Cashier V2 (CV2-01 → CV2-05) ═══
    {"id": "CV2-01", "module": "Cashier V2", "severity": "HIGH",
     "title": "Any user processes payment",
     "method": "GET", "path": "/process-payment",
     "params": {}, "needs_auth": True, "check": _check_unauth},
    {"id": "CV2-02", "module": "Cashier V2", "severity": "CRITICAL",
     "title": "serverPrint IDOR — print any receipt",
     "method": "GET", "path": "/cashier/server-print",
     "params": {"ornum": "00000", "studid": "0"}, "needs_auth": True, "check": _check_unauth},
    {"id": "CV2-03", "module": "Cashier V2", "severity": "HIGH",
     "title": "Void any suspended sale (IDOR)",
     "method": "GET", "path": "/cashier/suspended-sales",
     "params": {}, "needs_auth": True, "check": _check_json_data},
    {"id": "CV2-04", "module": "Cashier V2", "severity": "MEDIUM",
     "title": "Void permission structure leak",
     "method": "GET", "path": "/cashier/void/check-permission",
     "params": {}, "needs_auth": True, "check": _check_json_data},
    {"id": "CV2-05", "module": "Cashier V2", "severity": "HIGH",
     "title": "PIN brute force (cashier)",
     "method": "POST", "path": "/cashier/void/verify-pin",
     "params": {}, "body": {"pin": "0000", "pin_id": "1"},
     "needs_auth": True, "check": _check_action},

    # ═══ Student (ST-01 → ST-04) ═══
    {"id": "ST-01", "module": "Student", "severity": "CRITICAL",
     "title": "Scholarship upload (RCE vector)",
     "method": "GET", "path": "/uploadrequirement",
     "params": {}, "needs_auth": True, "check": _check_unauth},
    {"id": "ST-02", "module": "Student", "severity": "HIGH",
     "title": "Unauth SMS inject — notify_individual_student",
     "method": "GET", "path": "/student/notify_individual_student",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "ST-03", "module": "Student", "severity": "HIGH",
     "title": "Unauth financial dump — api_student_ledger_v2",
     "method": "GET", "path": "/api/mobile/api_student_ledger_v2",
     "params": {"studid": "1"}, "needs_auth": False, "check": _check_json_data},
    {"id": "ST-04", "module": "Student", "severity": "HIGH",
     "title": "Unauth grade dump — api_reportcard_v2",
     "method": "GET", "path": "/api/mobile/api_reportcard_v2",
     "params": {"studid": "1", "syid": "1"}, "needs_auth": False, "check": _check_json_data},

    # ═══ Registrar (R-01 → R-06) ═══
    {"id": "R-01", "module": "Registrar", "severity": "CRITICAL",
     "title": "Unauth account creation — fixAccountConflict",
     "method": "GET", "path": "/fixAccountConflict",
     "params": {}, "needs_auth": False, "check": _check_action},
    {"id": "R-02", "module": "Registrar", "severity": "CRITICAL",
     "title": "Unauth student enum — studentUserDebugger",
     "method": "GET", "path": "/studentUserDebugger",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "R-03", "module": "Registrar", "severity": "HIGH",
     "title": "Unauth enrollment manipulation",
     "method": "GET", "path": "/pre/enrollment/submit",
     "params": {"studid": "0"}, "needs_auth": False, "check": _check_action},
    {"id": "R-04", "module": "Registrar", "severity": "HIGH",
     "title": "Any user accesses RegistrarV2 config",
     "method": "GET", "path": "/registrarv2/setup/higher-education/colleges",
     "params": {}, "needs_auth": True, "check": _check_json_data},
    {"id": "R-06", "module": "Registrar", "severity": "MEDIUM",
     "title": "Pre-registration form (no rate limit)",
     "method": "GET", "path": "/prereg/newstudent",
     "params": {}, "needs_auth": False, "check": _check_unauth},

    # ═══ College (C-01 → C-06) ═══
    {"id": "C-01", "module": "College", "severity": "CRITICAL",
     "title": "Unauth grade corruption — /teacher/update/hps",
     "method": "GET", "path": "/teacher/update/hps",
     "params": {"a": "0", "b": "autoscan_probe", "c": "0"},
     "needs_auth": False, "check": _check_grade},
    {"id": "C-02", "module": "College", "severity": "HIGH",
     "title": "Any user modifies grades — /teacher/update/grades",
     "method": "GET", "path": "/teacher/update/grades",
     "params": {}, "needs_auth": True, "check": _check_grade},
    {"id": "C-03", "module": "College", "severity": "HIGH",
     "title": "Self-approve grades — ECR submit",
     "method": "GET", "path": "/college/grade/ecr/submit",
     "params": {}, "needs_auth": True, "check": _check_grade},
    {"id": "C-04", "module": "College", "severity": "HIGH",
     "title": "Remove subject from curriculum",
     "method": "GET", "path": "/dean/remove/prospectussubject/0",
     "params": {}, "needs_auth": True, "check": _check_unauth},
    {"id": "C-05", "module": "College", "severity": "HIGH",
     "title": "Unauth grade status submission",
     "method": "GET", "path": "/college/student/grade/status/submit",
     "params": {}, "needs_auth": False, "check": _check_grade},
    {"id": "C-06a", "module": "College", "severity": "HIGH",
     "title": "Unauth college grade dump",
     "method": "GET", "path": "/college/subject/students",
     "params": {"syid": "1", "semid": "1", "sectionid": "1", "subjid": "1"},
     "needs_auth": False, "check": _check_json_data},
    {"id": "C-06b", "module": "College", "severity": "HIGH",
     "title": "Unauth K-12 grade dump — /teacher/get/grades",
     "method": "GET", "path": "/teacher/get/grades/1/1",
     "params": {}, "needs_auth": False, "check": _check_json_data},

    # ═══ Parent (P-01 → P-02) ═══
    {"id": "P-01", "module": "Parent", "severity": "HIGH",
     "title": "Student bypasses isParent middleware",
     "method": "GET", "path": "/parent/enrollment/record/grades",
     "params": {"syid": "1", "semid": "1", "sectionid": "1", "levelid": "1"},
     "needs_auth": True, "check": _check_json_data},
    {"id": "P-02", "module": "Parent", "severity": "HIGH",
     "title": "Fake payment — parentEnterAmount",
     "method": "POST", "path": "/parentEnterAmount",
     "params": {}, "body": {}, "needs_auth": False, "check": _check_unauth},

    # ═══ Admin (A-01 → A-07) ═══
    {"id": "A-01", "module": "Admin", "severity": "CRITICAL",
     "title": "Unauth password reset — updatepass",
     "method": "GET", "path": "/administrator/setup/accounts/updatepass",
     "params": {"tid": "autoscan_nonexistent@fake.invalid"},
     "needs_auth": False, "check": _check_action},
    {"id": "A-02", "module": "Admin", "severity": "CRITICAL",
     "title": "Unauth plaintext password dump",
     "method": "GET", "path": "/administrator/setup/accounts/list",
     "params": {"status": "1", "length": "1", "start": "0"},
     "needs_auth": False, "check": _check_password_field},
    {"id": "A-03", "module": "Admin", "severity": "CRITICAL",
     "title": "Unauth account creation",
     "method": "GET", "path": "/administrator/setup/accounts/create/account",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "A-04", "module": "Admin", "severity": "HIGH",
     "title": "Unauth privilege grant",
     "method": "GET", "path": "/administrator/setup/accounts/update/privilege",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "A-05", "module": "Admin", "severity": "HIGH",
     "title": "Unauth account deactivation",
     "method": "GET", "path": "/administrator/setup/accounts/update/active",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "A-06a", "module": "Admin", "severity": "HIGH",
     "title": "Unauth grade approve",
     "method": "GET", "path": "/reportcard/grade/status/approve",
     "params": {}, "needs_auth": False, "check": _check_grade},
    {"id": "A-06b", "module": "Admin", "severity": "HIGH",
     "title": "Unauth grade post",
     "method": "GET", "path": "/reportcard/grade/status/post",
     "params": {}, "needs_auth": False, "check": _check_grade},
    {"id": "A-07", "module": "Admin", "severity": "HIGH",
     "title": "Unauth sync DB delete",
     "method": "GET", "path": "/administrator/setup/accounts/syncdelete",
     "params": {}, "needs_auth": False, "check": _check_unauth},

    # ═══ Principal (PR-01 → PR-05) ═══
    {"id": "PR-01a", "module": "Principal", "severity": "CRITICAL",
     "title": "Any auth user reads enrolled students",
     "method": "GET", "path": "/principal/section/students/enrolled",
     "params": {"section": "1", "acad": "3", "syid": "1", "gradelevel": "7"},
     "needs_auth": True, "check": _check_json_data},
    {"id": "PR-01b", "module": "Principal", "severity": "CRITICAL",
     "title": "Any auth user reads SF9 signatories",
     "method": "GET", "path": "/setup/signatories/list/sf9",
     "params": {"syid": "1"}, "needs_auth": True, "check": _check_json_data},
    {"id": "PR-02", "module": "Principal", "severity": "CRITICAL",
     "title": "Unauth deportment grade write",
     "method": "GET", "path": "/posting/grade/update-stud-gradstatus",
     "params": {}, "needs_auth": False, "check": _check_grade},
    {"id": "PR-03", "module": "Principal", "severity": "HIGH",
     "title": "Auth user self-approves grades",
     "method": "GET", "path": "/posting/grade/approve",
     "params": {}, "needs_auth": True, "check": _check_grade},
    {"id": "PR-04", "module": "Principal", "severity": "HIGH",
     "title": "Any user overwrites SF9 signatory",
     "method": "GET", "path": "/setup/signatories/update/sf9",
     "params": {}, "needs_auth": True, "check": _check_unauth},
    {"id": "PR-05", "module": "Principal", "severity": "MEDIUM",
     "title": "IDOR in section profile",
     "method": "GET", "path": "/principalPortalSectionProfile/1",
     "params": {}, "needs_auth": True, "check": _check_unauth},

    # ═══ Director (DR-02 → DR-03) ═══
    {"id": "DR-02", "module": "Director", "severity": "CRITICAL",
     "title": "Unauth employee PII — passData?action=getemployees",
     "method": "GET", "path": "/passData",
     "params": {"action": "getemployees"}, "needs_auth": False, "check": _check_json_data},
    {"id": "DR-03a", "module": "Director", "severity": "CRITICAL",
     "title": "Unauth finance — cashiertransactionsindex",
     "method": "GET", "path": "/director/finance/cashiertransactionsindex",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "DR-03b", "module": "Director", "severity": "CRITICAL",
     "title": "Unauth finance — collectionsindex",
     "method": "GET", "path": "/director/finance/collectionsindex",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "DR-03c", "module": "Director", "severity": "CRITICAL",
     "title": "Unauth finance — accountreceivablesindex",
     "method": "GET", "path": "/director/finance/accountreceivablesindex",
     "params": {}, "needs_auth": False, "check": _check_unauth},
    {"id": "DR-03d", "module": "Director", "severity": "HIGH",
     "title": "Unauth management dashboards",
     "method": "GET", "path": "/finance/index",
     "params": {}, "needs_auth": False, "check": _check_unauth},
]


# ── Scanner Engine ────────────────────────────────────────────────────────────

class AutoScanner:
    def __init__(self, base_url, session_cookie="", concurrency=10, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.session_cookie = session_cookie
        self.concurrency = concurrency
        self.timeout = timeout
        self.results = []
        self.login_info = None  # populated by auto_login()

    async def auto_login(self, email, password):
        """Authenticate against Laravel login and obtain session cookie automatically."""
        login_url = f"{self.base_url}/login"
        try:
            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as sess:
                # Step 1: GET /login to obtain CSRF token + XSRF cookie
                async with sess.get(login_url, ssl=False,
                                    timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                    html = await resp.text(errors='replace')

                # Extract CSRF token from <meta name="csrf-token" content="...">
                # or from <input type="hidden" name="_token" value="...">
                token = None
                m = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', html)
                if m:
                    token = m.group(1)
                else:
                    m = re.search(r'name="_token"\s+(?:type="hidden"\s+)?value="([^"]+)"', html)
                    if not m:
                        m = re.search(r'value="([^"]+)"\s+name="_token"', html)
                    if m:
                        token = m.group(1)

                if not token:
                    # Try XSRF-TOKEN cookie (Laravel sets it URL-encoded)
                    for cookie in jar:
                        if cookie.key == 'XSRF-TOKEN':
                            from urllib.parse import unquote
                            token = unquote(cookie.value)
                            break

                if not token:
                    return False, "Could not find CSRF token on login page"

                # Step 2: POST /login with credentials
                form_data = {
                    '_token': token,
                    'email': email,
                    'password': password,
                }
                headers = {
                    'Referer': login_url,
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
                async with sess.post(login_url, data=form_data, headers=headers,
                                     ssl=False, allow_redirects=False,
                                     timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                    status = resp.status

                    # Successful login = 302 redirect to /home
                    if status not in (301, 302, 303):
                        return False, f"Login failed (HTTP {status}) — check credentials"

                    # Extract laravel_session from Set-Cookie or cookie jar
                    session_val = None
                    for cookie in jar:
                        if 'session' in cookie.key.lower():
                            session_val = cookie.value
                            break

                    # Also check raw Set-Cookie headers
                    if not session_val:
                        for sc_header in resp.headers.getall('Set-Cookie', []):
                            m2 = re.search(r'laravel_session=([^;]+)', sc_header)
                            if m2:
                                session_val = m2.group(1)
                                break
                            # Some installs use a custom session name
                            m2 = re.search(r'([a-z_]*session[a-z_]*)=([^;]+)', sc_header)
                            if m2:
                                session_val = m2.group(2)
                                break

                    if not session_val:
                        return False, "Login redirected but no session cookie found"

                    self.session_cookie = session_val
                    self.login_info = {"email": email, "status": "authenticated"}
                    return True, f"Authenticated as {email}"

        except asyncio.TimeoutError:
            return False, "Login timed out"
        except aiohttp.ClientConnectorError as e:
            return False, f"Connection failed: {str(e)[:80]}"
        except Exception as e:
            return False, f"Login error: {str(e)[:80]}"

    def _headers(self, needs_auth):
        h = {"X-Requested-With": "XMLHttpRequest", "User-Agent": "MePwned-AutoScan/2.0"}
        if needs_auth and self.session_cookie:
            h["Cookie"] = f"laravel_session={self.session_cookie}"
        return h

    async def _run_one(self, session, test):
        url = f"{self.base_url}{test['path']}"
        method = test.get("method", "GET")
        params = test.get("params", {})
        needs_auth = test.get("needs_auth", False)
        headers = self._headers(needs_auth)
        check_fn = test["check"]

        if needs_auth and not self.session_cookie:
            return TestResult(test["id"], test["module"], test["severity"],
                              test["title"], "SKIPPED", "No session cookie")

        start = time.time()
        try:
            kwargs = dict(params=params, headers=headers,
                          timeout=aiohttp.ClientTimeout(total=self.timeout),
                          allow_redirects=False, ssl=False)

            if method == "POST":
                body_data = test.get("body", {})
                async with session.post(url, data=body_data, **kwargs) as resp:
                    sc = resp.status
                    if sc in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("Location", "")
                        rs, det = "PATCHED", f"Redirect → {loc[:50]}"
                    else:
                        body = await resp.text(errors='replace')
                        rs, det = check_fn(body[:8000], sc)
            else:
                async with session.get(url, **kwargs) as resp:
                    sc = resp.status
                    if sc in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("Location", "")
                        rs, det = "PATCHED", f"Redirect → {loc[:50]}"
                    else:
                        body = await resp.text(errors='replace')
                        rs, det = check_fn(body[:8000], sc)

            ms = round((time.time() - start) * 1000, 1)
            return TestResult(test["id"], test["module"], test["severity"],
                              test["title"], rs, det, sc, ms)

        except asyncio.TimeoutError:
            return TestResult(test["id"], test["module"], test["severity"],
                              test["title"], "UNREACHABLE", "Timeout")
        except aiohttp.ClientConnectorError as e:
            return TestResult(test["id"], test["module"], test["severity"],
                              test["title"], "UNREACHABLE", str(e)[:100])
        except Exception as e:
            return TestResult(test["id"], test["module"], test["severity"],
                              test["title"], "ERROR", str(e)[:100])

    async def run_all(self, progress_cb=None):
        sem = asyncio.Semaphore(self.concurrency)
        conn = aiohttp.TCPConnector(limit=self.concurrency, ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            async def bounded(test):
                async with sem:
                    r = await self._run_one(session, test)
                    self.results.append(r)
                    if progress_cb:
                        progress_cb(r)
                    return r
            await asyncio.gather(*[bounded(t) for t in TESTS])

    def build_report(self):
        vuln = sum(1 for r in self.results if r.status == "VULNERABLE")
        patched = sum(1 for r in self.results if r.status == "PATCHED")
        err = sum(1 for r in self.results if r.status == "ERROR")
        unreach = sum(1 for r in self.results if r.status == "UNREACHABLE")
        skip = sum(1 for r in self.results if r.status == "SKIPPED")
        tested = len(self.results) - skip

        crit_v = sum(1 for r in self.results if r.status == "VULNERABLE" and r.severity == "CRITICAL")
        high_v = sum(1 for r in self.results if r.status == "VULNERABLE" and r.severity == "HIGH")
        med_v = sum(1 for r in self.results if r.status == "VULNERABLE" and r.severity == "MEDIUM")

        modules = {}
        for r in self.results:
            m = modules.setdefault(r.module, {"total": 0, "vulnerable": 0, "patched": 0, "other": 0})
            m["total"] += 1
            if r.status == "VULNERABLE": m["vulnerable"] += 1
            elif r.status == "PATCHED": m["patched"] += 1
            else: m["other"] += 1

        risk = round((crit_v * 10 + high_v * 5 + med_v * 2) / max(tested, 1) * 10, 1)

        return ScanReport(
            target_url=self.base_url,
            scan_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            results=[asdict(r) for r in sorted(self.results, key=lambda x: (
                {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x.severity, 3),
                {"VULNERABLE": 0, "ERROR": 1, "UNREACHABLE": 2, "SKIPPED": 3, "PATCHED": 4}.get(x.status, 5),
            ))],
            summary={
                "total_tests": len(self.results), "vulnerable": vuln, "patched": patched,
                "error": err, "unreachable": unreach, "skipped": skip,
                "critical_vulnerable": crit_v, "high_vulnerable": high_v,
                "medium_vulnerable": med_v, "risk_score": risk,
                "patch_rate": round(patched / max(tested, 1) * 100, 1),
                "modules": modules,
            }
        )


# ── CLI Output ────────────────────────────────────────────────────────────────

def print_progress(result):
    icons = {"VULNERABLE": f"{RED}■", "PATCHED": f"{GREEN}■",
             "ERROR": f"{YELLOW}■", "UNREACHABLE": f"{DIM}■", "SKIPPED": f"{DIM}○"}
    sev_c = {"CRITICAL": RED, "HIGH": YELLOW, "MEDIUM": CYAN, "LOW": DIM}
    icon = icons.get(result.status, f"{DIM}?")
    sc = sev_c.get(result.severity, DIM)
    ms = f"{result.response_time_ms:.0f}ms" if result.response_time_ms else "---"
    stat = result.status[:4]
    print(f"  {icon}{RESET} {sc}{result.severity:8}{RESET} {stat:4} {result.finding_id:7} "
          f"{result.title[:48]:<48} {DIM}{ms}{RESET}")


def print_summary(report):
    s = report.summary
    pct = s["patch_rate"]
    risk = s["risk_score"]

    print(f"\n  {'━' * 62}")
    print(f"  {BOLD}SCAN COMPLETE{RESET}  {report.target_url}")
    print(f"  {'━' * 62}\n")
    print(f"   Total:       {s['total_tests']}")
    print(f"   {RED}Vulnerable:  {s['vulnerable']}{RESET} "
          f"({s['critical_vulnerable']}C / {s['high_vulnerable']}H / {s['medium_vulnerable']}M)")
    print(f"   {GREEN}Patched:     {s['patched']}{RESET}")
    print(f"   {DIM}Skip/Err:    {s['skipped']} / {s['error']} / {s['unreachable']}{RESET}")
    print(f"\n   Patch Rate:  {GREEN if pct > 70 else YELLOW if pct > 40 else RED}{pct:.1f}%{RESET}")
    print(f"   Risk Score:  {RED if risk > 50 else YELLOW if risk > 20 else GREEN}{risk}/100{RESET}")
    print(f"\n  {'─' * 62}")
    print(f"  {'Module':<16} {'Vuln':>5} {'Safe':>5} {'Other':>5}  Status")
    print(f"  {'─' * 62}")
    for mod, d in sorted(report.summary["modules"].items()):
        v, p, o = d["vulnerable"], d["patched"], d["other"]
        st = f"{GREEN}CLEAR{RESET}" if v == 0 else (f"{RED}EXPOSED{RESET}" if p == 0 else f"{YELLOW}PARTIAL{RESET}")
        print(f"  {mod:<16} {RED}{v:>5}{RESET} {GREEN}{p:>5}{RESET} {DIM}{o:>5}{RESET}  {st}")
    print(f"  {'─' * 62}\n")


def build_markdown(report):
    s = report.summary
    lines = [
        "# AutoScan Security Verification Report",
        f"**Target:** `{report.target_url}`  ",
        f"**Date:** {report.scan_date} | **Duration:** {report.scan_duration_sec:.1f}s\n",
        "## Summary", "| Metric | Value |", "|---|---|",
        f"| Tests | {s['total_tests']} |",
        f"| **Vulnerable** | **{s['vulnerable']}** |",
        f"| Patched | {s['patched']} |",
        f"| Patch Rate | {s['patch_rate']:.1f}% |",
        f"| Risk Score | {s['risk_score']}/100 |",
        "", "## Modules", "| Module | Vuln | Safe | Status |", "|---|---|---|---|",
    ]
    for mod, d in sorted(s["modules"].items()):
        v, p = d["vulnerable"], d["patched"]
        st = "CLEAR" if v == 0 else ("EXPOSED" if p == 0 else "PARTIAL")
        lines.append(f"| {mod} | {v} | {p} | {st} |")

    vuln_r = [r for r in report.results if r["status"] == "VULNERABLE"]
    if vuln_r:
        lines += ["", "## Vulnerable Endpoints",
                  "| ID | Severity | Module | Title | Detail |", "|---|---|---|---|---|"]
        for r in vuln_r:
            lines.append(f"| {r['finding_id']} | **{r['severity']}** | {r['module']} | {r['title']} | {r['detail']} |")

    lines += ["", "---", "*MePwned AutoScan v2.0*"]
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="MePwned AutoScan v2.0")
    parser.add_argument("--url", help="Target base URL")
    parser.add_argument("--email", default="", help="Login email/username (auto-login)")
    parser.add_argument("--password", default="", help="Login password (auto-login)")
    parser.add_argument("--session", default="", help="laravel_session cookie (skip login)")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json", default="", help="JSON output file")
    parser.add_argument("--md", default="", help="Markdown output file")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    print(BANNER)

    base_url = args.url
    if not base_url:
        try:
            base_url = input(f"  {CYAN}Target URL:{RESET} ").strip().rstrip("/")
        except KeyboardInterrupt:
            return
    if not base_url:
        print(f"  {RED}No URL.{RESET}"); return

    # ── Authentication: auto-login or manual session ──
    session = args.session
    email = args.email
    password = args.password

    if not session and not email and not args.quiet:
        print(f"\n  {CYAN}Authentication:{RESET}")
        print(f"  {DIM}1) Enter credentials (auto-login){RESET}")
        print(f"  {DIM}2) Paste session cookie{RESET}")
        print(f"  {DIM}3) Skip (unauth tests only){RESET}")
        try:
            choice = input(f"  {CYAN}Choice [1/2/3]:{RESET} ").strip()
        except KeyboardInterrupt:
            return
        if choice == "1":
            try:
                email = input(f"  {CYAN}Email/Username:{RESET} ").strip()
                password = input(f"  {CYAN}Password:{RESET} ").strip()
            except KeyboardInterrupt:
                return
        elif choice == "2":
            try:
                session = input(f"  {CYAN}Session cookie:{RESET} ").strip()
            except KeyboardInterrupt:
                pass

    # Create scanner early so we can use auto_login
    scanner = AutoScanner(base_url, session, args.concurrency, args.timeout)

    # Auto-login if credentials provided
    if email and password and not session:
        print(f"\n  {CYAN}Authenticating...{RESET}", end=" ", flush=True)
        ok, msg = await scanner.auto_login(email, password)
        if ok:
            print(f"{GREEN}✓ {msg}{RESET}")
            session = scanner.session_cookie
        else:
            print(f"{RED}✗ {msg}{RESET}")
            print(f"  {YELLOW}Continuing with unauth tests only{RESET}")

    u = sum(1 for t in TESTS if not t["needs_auth"])
    a = sum(1 for t in TESTS if t["needs_auth"])
    print(f"\n  Target:   {base_url}")
    print(f"  Checks:   {len(TESTS)} ({u} unauth + {a} auth)")
    print(f"  Session:  {'yes' if scanner.session_cookie else 'no (auth tests skipped)'}")
    print(f"\n  {'─' * 62}\n")

    t0 = time.time()
    await scanner.run_all(progress_cb=None if args.quiet else print_progress)
    elapsed = time.time() - t0

    report = scanner.build_report()
    report.scan_duration_sec = round(elapsed, 1)
    print_summary(report)

    json_path = args.json
    if not json_path and not args.quiet:
        try:
            json_path = input(f"  {CYAN}Save JSON?{RESET} (filename or Enter): ").strip()
        except KeyboardInterrupt:
            json_path = ""
    if json_path:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        print(f"  Saved: {json_path}")

    md_path = args.md
    if not md_path and not args.quiet:
        try:
            md_path = input(f"  {CYAN}Save Markdown?{RESET} (filename or Enter): ").strip()
        except KeyboardInterrupt:
            md_path = ""
    if md_path:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(build_markdown(report))
        print(f"  Saved: {md_path}")

    print(f"\n  {DIM}Done in {elapsed:.1f}s{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
