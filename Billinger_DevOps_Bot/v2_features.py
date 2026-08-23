"""Billinger v2 realism features.

Standard-library only. All default operations remain local, deterministic and safe.
Optional integrations are restricted to localhost and read-only/sandboxed commands.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import platform
import random
import re
import secrets
import shlex
import shutil
import sqlite3
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
DATA_DIR = BASE_DIR / "data"
LAB_DIR = BASE_DIR / "labs"
DB_PATH = Path(os.environ.get("BILLINGER_DB_PATH", str(DATA_DIR / "billinger.db"))).resolve()
COMPANY = json.loads((CONTENT_DIR / "company_scenarios.json").read_text(encoding="utf-8"))
INTERVIEW_DATA = json.loads((CONTENT_DIR / "interview_bank.json").read_text(encoding="utf-8"))
QUESTION_DATA = json.loads((CONTENT_DIR / "question_bank.json").read_text(encoding="utf-8"))
LEVELS = ["Beginner", "Intermediate", "Advanced", "Master"]
PASS_MARKS = {"Beginner": 70, "Intermediate": 75, "Advanced": 80, "Master": 85}

SCHEMA_V2 = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS company_ticket_runs (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    ticket_id TEXT NOT NULL,
    status TEXT NOT NULL,
    response TEXT NOT NULL DEFAULT '',
    standup TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    rubric_json TEXT NOT NULL DEFAULT '{}',
    feedback TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS incident_runs (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    incident_id TEXT NOT NULL,
    status TEXT NOT NULL,
    response TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    feedback TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS lab_runs (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    command TEXT NOT NULL,
    output TEXT NOT NULL,
    exit_code INTEGER NOT NULL,
    safety TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS recruitment_sessions (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    target_role TEXT NOT NULL,
    track TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    resume_text TEXT NOT NULL DEFAULT '',
    job_description TEXT NOT NULL DEFAULT '',
    state_json TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    passed INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS capstone_runs (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    capstone_id TEXT NOT NULL,
    submission TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    rubric_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,
    feedback TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS coaching_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    tool TEXT NOT NULL,
    note_type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
"""

DEFAULT_SETTINGS = {
    "ai_enabled": False,
    "ai_endpoint": "http://127.0.0.1:8080/v1/chat/completions",
    "ai_model": "local-model",
    "ai_timeout_seconds": 45,
    "lab_mode": "simulator",
    "wsl_distribution": "",
    "voice_enabled": True,
    "company_name": "Billinger Technologies",
}

ALLOWED_SIMPLE = {
    "pwd", "ls", "dir", "whoami", "hostname", "date", "echo", "mkdir", "touch", "cat", "type",
    "head", "tail", "wc", "sort", "uniq", "grep", "find", "tree", "git", "python", "py", "where",
    "docker", "kubectl", "terraform", "ansible", "ansible-config", "ansible-doc",
}
ALLOWED_SUBCOMMANDS = {
    "git": {"status", "log", "diff", "branch", "show", "rev-parse", "remote"},
    "docker": {"version", "info", "ps", "images", "inspect", "logs", "stats"},
    "kubectl": {"version", "cluster-info", "get", "describe", "logs", "config", "api-resources", "explain", "top"},
    "terraform": {"version", "validate", "fmt", "providers", "show", "output", "graph"},
    "ansible": {"--version", "version", "inventory", "config", "doc"},
    "ansible-config": {"list", "dump", "view"},
    "ansible-doc": {"--list", "--version"},
    "python": {"--version", "-V"},
    "py": {"--version", "-V"},
}
BLOCKED_TOKENS = {";", "&&", "||", "|", ">", "<", "`", "$(", "sudo", " rmdir", " del ", " erase ", " shutdown", " reboot", " kill", "taskkill", " reg ", " sc ", " curl", " wget", " ssh", " scp", "powershell", "cmd.exe"}
BLOCKED_ARGUMENTS = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "--delete", "--force", "--privileged", "--mount", "--volume", "-v"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


class ClosingConnection(sqlite3.Connection):
    """SQLite connection that commits/rolls back and closes at context exit."""
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        try:
            return bool(super().__exit__(exc_type, exc, tb))
        finally:
            self.close()


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_v2_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LAB_DIR.mkdir(parents=True, exist_ok=True)
    with db_connect() as conn:
        conn.executescript(SCHEMA_V2)
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO app_settings(key,value,updated_at) VALUES(?,?,?)",
                (key, json.dumps(value), now_iso()),
            )


def clean_text(value: Any, max_len: int = 100_000) -> str:
    return str(value or "").replace("\x00", "").strip()[:max_len]


def normalize_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9+.#_-]{2,}", text.lower())


def get_settings() -> dict[str, Any]:
    out = dict(DEFAULT_SETTINGS)
    with db_connect() as conn:
        for row in conn.execute("SELECT key,value FROM app_settings"):
            try:
                out[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                out[row["key"]] = row["value"]
    return out


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    allowed = set(DEFAULT_SETTINGS)
    settings = get_settings()
    with db_connect() as conn:
        for key, value in data.items():
            if key not in allowed:
                continue
            if key == "ai_endpoint":
                value = clean_text(value, 500)
                parsed = urllib.parse.urlparse(value)
                if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
                    raise ValueError("AI endpoint must be a localhost address.")
            if key == "lab_mode" and value not in {"simulator", "windows", "wsl"}:
                raise ValueError("Invalid lab mode.")
            settings[key] = value
            conn.execute(
                "INSERT INTO app_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                (key, json.dumps(value), now_iso()),
            )
    return settings


def _rowdict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return None if row is None else {k: row[k] for k in row.keys()}


def _ticket_map() -> dict[str, dict[str, Any]]:
    return {x["id"]: x for x in COMPANY["tickets"]}


def _incident_map() -> dict[str, dict[str, Any]]:
    return {x["id"]: x for x in COMPANY["incidents"]}


def _score_rubric(answer: str, keywords: list[str], *, incident: bool = False) -> tuple[float, dict[str, float], list[str]]:
    text = answer.lower()
    tokens = set(normalize_tokens(answer))
    matched = [k for k in keywords if (k.lower() in text if " " in k else k.lower() in tokens or k.lower() in text)]
    coverage = min(100.0, len(matched) / max(1, len(keywords)) * 100)
    word_count = len(normalize_tokens(answer))
    correctness = min(100.0, coverage * 0.82 + min(18, word_count / 5))
    diagnostic = 100.0 if all(x in text for x in ("evidence", "hypothesis")) else (75.0 if any(x in text for x in ("log", "metric", "inspect", "diagnos")) else 35.0)
    validation = 100.0 if any(x in text for x in ("validate", "verify", "test", "health check", "evidence")) else 25.0
    security = 100.0 if any(x in text for x in ("least privilege", "secret", "security", "permission", "scan", "policy")) else 45.0
    rollback = 100.0 if any(x in text for x in ("rollback", "restore", "snapshot", "revert", "backup")) else 20.0
    communication = 100.0 if any(x in text for x in ("stakeholder", "stand-up", "manager", "communicat", "status update", "approval")) else 35.0
    business = 100.0 if any(x in text for x in ("customer", "revenue", "impact", "sla", "slo", "business")) else 35.0
    if incident:
        weights = {"technical": .25, "diagnosis": .20, "validation": .12, "security": .08, "rollback": .15, "communication": .12, "business": .08}
    else:
        weights = {"technical": .30, "diagnosis": .15, "validation": .15, "security": .10, "rollback": .12, "communication": .10, "business": .08}
    rubric = {
        "technical": round(correctness, 1), "diagnosis": diagnostic, "validation": validation,
        "security": security, "rollback": rollback, "communication": communication, "business": business,
    }
    score = round(sum(rubric[k] * weights[k] for k in weights), 1)
    missing = [k for k in keywords if k not in matched][:12]
    return score, rubric, missing


def company_overview(student_id: int) -> dict[str, Any]:
    tickets = COMPANY["tickets"]
    incidents = COMPANY["incidents"]
    with db_connect() as conn:
        runs = conn.execute("SELECT ticket_id,status,score,updated_at FROM company_ticket_runs WHERE student_id=? ORDER BY updated_at DESC", (student_id,)).fetchall()
        iruns = conn.execute("SELECT incident_id,status,score,updated_at FROM incident_runs WHERE student_id=? ORDER BY updated_at DESC", (student_id,)).fetchall()
    run_map = {r["ticket_id"]: _rowdict(r) for r in runs}
    irun_map = {r["incident_id"]: _rowdict(r) for r in iruns}
    recommended = []
    for t in tickets:
        state = run_map.get(t["id"])
        if not state or state["status"] != "passed":
            recommended.append({**t, "run": state})
        if len(recommended) >= 6:
            break
    active_incidents = [{**i, "run": irun_map.get(i["id"])} for i in incidents[:4]]
    passed = sum(1 for r in runs if r["status"] == "passed")
    avg = round(sum(float(r["score"]) for r in runs) / len(runs), 1) if runs else 0
    return {
        "company": COMPANY["company"], "manager_message": "Good engineering is evidence-driven: understand impact, inspect before changing, validate after changing, and always retain a safe recovery path.",
        "standup_questions": COMPANY["standup_questions"], "recommended_tickets": recommended,
        "active_incidents": active_incidents, "performance": {"tickets_passed": passed, "attempts": len(runs), "average_score": avg},
        "service_health": [
            {"name": "Customer API", "status": "healthy", "slo": "99.95%", "latency": "142 ms"},
            {"name": "Checkout", "status": "degraded", "slo": "99.90%", "latency": "486 ms"},
            {"name": "CI/CD Platform", "status": "healthy", "slo": "99.80%", "latency": "31 s queue"},
        ],
    }


def get_ticket(ticket_id: str) -> dict[str, Any]:
    item = _ticket_map().get(ticket_id)
    if not item:
        raise ValueError("Company ticket not found.")
    return item


def submit_ticket(student_id: int, ticket_id: str, response: str, standup: str = "") -> dict[str, Any]:
    ticket = get_ticket(ticket_id)
    response = clean_text(response, 40_000)
    standup = clean_text(standup, 8_000)
    if len(response) < 80:
        raise ValueError("Provide a complete implementation plan with evidence, risks, validation, and rollback.")
    score, rubric, missing = _score_rubric(response + "\n" + standup, ticket["keywords"])
    passed = score >= PASS_MARKS.get(ticket["level"], 75)
    feedback = ("Ticket accepted by reviewer." if passed else "Reviewer requested changes.")
    feedback += " Strongest dimensions: " + ", ".join(k for k, v in sorted(rubric.items(), key=lambda x: x[1], reverse=True)[:2]) + "."
    if missing:
        feedback += " Add clearer coverage for: " + ", ".join(missing[:8]) + "."
    run_id = f"CTR-{secrets.token_hex(8)}"
    ts = now_iso()
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO company_ticket_runs(id,student_id,ticket_id,status,response,standup,score,rubric_json,feedback,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, student_id, ticket_id, "passed" if passed else "needs_review", response, standup, score, json.dumps(rubric), feedback, ts, ts),
        )
        conn.execute("INSERT INTO audit_log(student_id,action,detail,created_at) VALUES(?,?,?,?)", (student_id, "company_ticket_submitted", f"{ticket_id};score={score}", ts))
    return {"id": run_id, "ticket": ticket, "score": score, "passed": passed, "rubric": rubric, "missing": missing, "feedback": feedback}


def submit_incident(student_id: int, incident_id: str, response: str) -> dict[str, Any]:
    incident = _incident_map().get(incident_id)
    if not incident:
        raise ValueError("Incident not found.")
    response = clean_text(response, 40_000)
    if len(response) < 100:
        raise ValueError("Provide the incident timeline, evidence, diagnosis, mitigation, communications, and post-incident actions.")
    score, rubric, missing = _score_rubric(response, incident["keywords"], incident=True)
    passed = score >= 78
    feedback = ("Incident response passed the review." if passed else "Incident response needs stronger operational discipline.")
    if rubric["diagnosis"] < 70:
        feedback += " Collect evidence and state a testable hypothesis before mitigation."
    if rubric["communication"] < 70:
        feedback += " Add stakeholder updates and clear ownership."
    if rubric["rollback"] < 70:
        feedback += " Define a safe rollback trigger and verification plan."
    run_id = f"IR-{secrets.token_hex(8)}"; ts = now_iso()
    with db_connect() as conn:
        conn.execute("INSERT INTO incident_runs(id,student_id,incident_id,status,response,score,feedback,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                     (run_id, student_id, incident_id, "passed" if passed else "needs_review", response, score, feedback, ts, ts))
        conn.execute("INSERT INTO audit_log(student_id,action,detail,created_at) VALUES(?,?,?,?)", (student_id, "incident_simulation", f"{incident_id};score={score}", ts))
    return {"id": run_id, "incident": incident, "score": score, "passed": passed, "rubric": rubric, "missing": missing, "feedback": feedback}


def _is_safe_relative_path(value: str) -> bool:
    value = value.replace("\\", "/")
    if not value or value.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", value):
        return False
    parts = [x for x in value.split("/") if x not in ("", ".")]
    return bool(parts) and ".." not in parts and not any("*" in x or "?" in x for x in parts)


def _safe_command_parts(command: str) -> list[str]:
    command = clean_text(command, 500)
    if not command:
        raise ValueError("Enter a command.")
    lowered = " " + command.lower() + " "
    for token in BLOCKED_TOKENS:
        if token in lowered:
            raise ValueError(f"Blocked unsafe token: {token.strip()}")
    parts = shlex.split(command, posix=platform.system() != "Windows")
    if not parts or parts[0].lower() not in ALLOWED_SIMPLE:
        raise ValueError("This command is not in the safe learning allowlist.")
    if len(parts) > 20:
        raise ValueError("Command is too complex for safe lab mode.")
    cmd = parts[0].lower(); args = parts[1:]
    if any(arg.lower() in BLOCKED_ARGUMENTS for arg in args):
        raise ValueError("A destructive or host-access argument was blocked.")
    if cmd in ALLOWED_SUBCOMMANDS:
        if not args or args[0] not in ALLOWED_SUBCOMMANDS[cmd]:
            raise ValueError(f"Only approved read-only {cmd} subcommands are allowed.")
    if cmd == "kubectl":
        joined = " ".join(args).lower()
        if any(x in joined for x in (" secret", " secrets", "--raw", "--token", "exec", "apply", "delete", "patch", "edit", "scale", "rollout restart")):
            raise ValueError("This Kubernetes operation is not permitted in safe mode.")
    if cmd in {"mkdir", "touch", "cat", "type", "head", "tail", "wc", "sort", "uniq", "grep", "find", "tree", "ls", "dir"}:
        for arg in args:
            if arg.startswith("-"):
                continue
            # grep's first non-option argument is a pattern; other path arguments must still be local.
            if cmd == "grep" and arg == next((x for x in args if not x.startswith("-")), None):
                continue
            if not _is_safe_relative_path(arg):
                raise ValueError("File access is restricted to relative paths inside the student workspace.")
    return parts


def _simulate_command(parts: list[str], workspace: Path) -> tuple[str, int]:
    cmd = parts[0].lower(); args = parts[1:]
    if cmd in {"pwd"}:
        return str(workspace), 0
    if cmd in {"ls", "dir", "tree"}:
        files = sorted(p.name + ("/" if p.is_dir() else "") for p in workspace.iterdir())
        return "\n".join(files) if files else "(workspace is empty)", 0
    if cmd in {"whoami"}:
        return "billinger-student", 0
    if cmd == "hostname":
        return "billinger-lab", 0
    if cmd == "date":
        return dt.datetime.now().astimezone().isoformat(timespec="seconds"), 0
    if cmd == "echo":
        return " ".join(args), 0
    if cmd == "mkdir":
        if not args: return "mkdir: missing operand", 2
        for name in args:
            safe = Path(name).name
            (workspace / safe).mkdir(exist_ok=True)
        return "created: " + ", ".join(Path(x).name for x in args), 0
    if cmd == "touch":
        if not args: return "touch: missing file operand", 2
        for name in args:
            (workspace / Path(name).name).touch()
        return "updated timestamps: " + ", ".join(Path(x).name for x in args), 0
    if cmd in {"cat", "type", "head", "tail"}:
        if not args: return f"{cmd}: missing file operand", 2
        p = workspace / Path(args[-1]).name
        if not p.is_file(): return f"{cmd}: {p.name}: No such file", 1
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if cmd == "head": lines = lines[:10]
        if cmd == "tail": lines = lines[-10:]
        return "\n".join(lines)[:8000], 0
    if cmd == "git":
        sub = args[0].lower() if args else ""
        if sub == "status": return "On branch main\nYour branch is up to date with 'origin/main'.\n\nnothing to commit, working tree clean", 0
        if sub == "branch": return "* main\n  feature/student-lab", 0
        if sub == "log": return "a4e91d2 (HEAD -> main) Add health check\n5bd120a Configure CI validation\n812ef90 Initial lab project", 0
        if sub == "diff": return "diff --git a/deployment.yaml b/deployment.yaml\n+ readinessProbe:\n+   httpGet:\n+     path: /health", 0
        return "Safe simulator supports: git status, branch, log, diff", 0
    if cmd in {"python", "py"} and args == ["--version"]:
        return f"Python {platform.python_version()}", 0
    if cmd == "where":
        return "Simulator: executable discovery is available only in Windows/WSL mode.", 0
    return f"Simulated safely: {' '.join(parts)}\nNo host system changes were made.", 0


def run_lab_command(student_id: int, command: str, mode: str | None = None) -> dict[str, Any]:
    settings = get_settings(); mode = mode or settings.get("lab_mode", "simulator")
    if mode not in {"simulator", "windows", "wsl"}:
        raise ValueError("Invalid lab mode.")
    parts = _safe_command_parts(command)
    workspace = LAB_DIR / f"student_{student_id}"
    workspace.mkdir(parents=True, exist_ok=True)
    output = ""; code = 0; safety = "isolated simulator"
    if mode == "simulator":
        output, code = _simulate_command(parts, workspace)
    elif mode == "windows":
        if platform.system() != "Windows":
            raise ValueError("Windows command mode is available only on Windows. Use simulator mode here.")
        executable = shutil.which(parts[0])
        if not executable:
            raise ValueError(f"Command not installed: {parts[0]}")
        result = subprocess.run([executable, *parts[1:]], cwd=workspace, capture_output=True, text=True, timeout=12, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        output = (result.stdout + result.stderr)[:12000]; code = result.returncode; safety = "allowlisted Windows process in student workspace"
    else:
        if platform.system() != "Windows" or not shutil.which("wsl.exe"):
            raise ValueError("WSL is not available. Enable WSL or use simulator mode.")
        # Pass arguments without shell metacharacters. The command executes in a dedicated mounted workspace.
        win_path = str(workspace.resolve())
        distro = clean_text(settings.get("wsl_distribution"), 80)
        prefix = ["wsl.exe"] + (["-d", distro] if distro else [])
        result = subprocess.run(prefix + ["--cd", win_path, "--", *parts], capture_output=True, text=True, timeout=12, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        output = (result.stdout + result.stderr)[:12000]; code = result.returncode; safety = "allowlisted WSL process in student workspace"
    run_id = f"LAB-{secrets.token_hex(8)}"; ts = now_iso()
    with db_connect() as conn:
        conn.execute("INSERT INTO lab_runs(id,student_id,mode,command,output,exit_code,safety,created_at) VALUES(?,?,?,?,?,?,?,?)",
                     (run_id, student_id, mode, command, output, code, safety, ts))
        conn.execute("INSERT INTO audit_log(student_id,action,detail,created_at) VALUES(?,?,?,?)", (student_id, "safe_lab_command", f"mode={mode};exit={code};cmd={command[:120]}", ts))
    return {"id": run_id, "mode": mode, "command": command, "output": output or "(no output)", "exit_code": code, "safety": safety, "workspace": str(workspace)}


def _score_rows(student_id: int) -> dict[str, dict[str, float]]:
    scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    with db_connect() as conn:
        catalog = json.loads((CONTENT_DIR / "devops_catalog.json").read_text(encoding="utf-8"))
        slugs = sorted((t["slug"] for t in catalog["tools"]), key=len, reverse=True)
        for r in conn.execute("SELECT item_type,item_id,score,status FROM progress WHERE student_id=?", (student_id,)):
            item_id = r["item_id"]
            tool = next((slug for slug in slugs if item_id.startswith(slug + "-")), item_id.split("-")[0])
            dim = "knowledge" if r["item_type"] == "lesson" else "practice"
            scores[tool][dim].append(100.0 if r["item_type"] == "lesson" and r["status"] == "completed" else float(r["score"]))
        for r in conn.execute("SELECT tool,score FROM test_sessions WHERE student_id=? AND completed_at!=''", (student_id,)):
            scores[r["tool"]]["test"].append(float(r["score"]))
        for r in conn.execute("SELECT tool,score FROM interview_sessions WHERE student_id=? AND status='completed'", (student_id,)):
            scores[r["tool"]]["interview"].append(float(r["score"]))
        ticket_lookup = _ticket_map()
        for r in conn.execute("SELECT ticket_id,score FROM company_ticket_runs WHERE student_id=?", (student_id,)):
            t = ticket_lookup.get(r["ticket_id"])
            if t: scores[t["tool"]]["company"].append(float(r["score"]))
    out = {}
    for tool, dims in scores.items():
        out[tool] = {d: round(sum(v) / len(v), 1) for d, v in dims.items() if v}
    return out


def skill_matrix(student_id: int) -> dict[str, Any]:
    score_rows = _score_rows(student_id)
    tools = []
    catalog = json.loads((CONTENT_DIR / "devops_catalog.json").read_text(encoding="utf-8"))
    for t in catalog["tools"]:
        dims = score_rows.get(t["slug"], {})
        values = {
            "knowledge": dims.get("knowledge", 0), "practice": dims.get("practice", 0), "test": dims.get("test", 0),
            "interview": dims.get("interview", 0), "company": dims.get("company", 0),
        }
        overall = round(values["knowledge"]*.25 + values["practice"]*.22 + values["test"]*.20 + values["interview"]*.18 + values["company"]*.15, 1)
        if overall >= 85: level = "Master-ready"
        elif overall >= 70: level = "Professional"
        elif overall >= 50: level = "Developing"
        elif overall > 0: level = "Foundation"
        else: level = "Not started"
        tools.append({"slug": t["slug"], "name": t["name"], "icon": t["icon"], **values, "overall": overall, "level": level})
    weak = sorted(tools, key=lambda x: x["overall"])[:5]
    strong = sorted(tools, key=lambda x: x["overall"], reverse=True)[:5]
    return {"tools": tools, "weakest": weak, "strongest": strong, "recommendation": "Complete the next lesson and company ticket in your weakest active domain, then retest after practice."}


def system_readiness() -> dict[str, Any]:
    settings = get_settings()
    def which(name: str) -> bool: return shutil.which(name) is not None
    total_ram_gb = None
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output(["wmic", "ComputerSystem", "get", "TotalPhysicalMemory", "/value"], text=True, timeout=3)
            m = re.search(r"TotalPhysicalMemory=(\d+)", out); total_ram_gb = round(int(m.group(1))/1024**3, 1) if m else None
        elif hasattr(os, "sysconf"):
            total_ram_gb = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3, 1)
    except Exception:
        pass
    ai_ok = False; ai_detail = "Disabled"
    if settings.get("ai_enabled"):
        try:
            parsed = urllib.parse.urlparse(str(settings.get("ai_endpoint")))
            ai_ok = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
            ai_detail = "Configured on localhost" if ai_ok else "Invalid non-local endpoint"
        except Exception:
            ai_detail = "Invalid endpoint"
    return {
        "os": platform.platform(), "python": platform.python_version(), "ram_gb": total_ram_gb,
        "core": {"ready": True, "detail": "Standard-library local engine"},
        "git": {"ready": which("git"), "detail": "Detected" if which("git") else "Optional"},
        "wsl": {"ready": which("wsl.exe") if platform.system()=="Windows" else False, "detail": "Detected" if which("wsl.exe") else "Optional; simulator remains available"},
        "docker": {"ready": which("docker"), "detail": "Detected" if which("docker") else "Optional"},
        "kubectl": {"ready": which("kubectl"), "detail": "Detected" if which("kubectl") else "Optional"},
        "terraform": {"ready": which("terraform"), "detail": "Detected" if which("terraform") else "Optional"},
        "local_ai": {"ready": ai_ok, "detail": ai_detail},
        "settings": settings,
    }


def local_ai_chat(messages: list[dict[str, str]], purpose: str = "coach") -> dict[str, Any]:
    settings = get_settings()
    if not settings.get("ai_enabled"):
        raise ValueError("Local AI is disabled. Enable it in System Readiness after starting a localhost model server.")
    endpoint = str(settings.get("ai_endpoint"))
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Only localhost AI endpoints are allowed.")
    system = {
        "role": "system",
        "content": "You are the Billinger local DevOps coach. Be evidence-driven, technically precise, safe, and concise. Never invent candidate experience. For operational tasks require validation and rollback.",
    }
    payload = json.dumps({"model": settings.get("ai_model", "local-model"), "messages": [system, *messages], "temperature": 0.3, "max_tokens": 900}).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json", "User-Agent": "BillingerBot/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=int(settings.get("ai_timeout_seconds", 45))) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError(f"Local AI server could not be reached: {exc}") from exc
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise ValueError("Local AI returned an unsupported response.") from exc
    return {"content": clean_text(content, 20_000), "purpose": purpose, "local_only": True}


def _recruitment_questions(track: str, difficulty: str, resume_text: str, job_description: str) -> list[dict[str, Any]]:
    rounds = ["Screening", "HR", "Technical Fundamentals", "Company Scenario", "Troubleshooting", "Coding & Scripting", "System Design", "Managerial", "Final HR"]
    pool = [q for q in INTERVIEW_DATA["questions"] if (track == "full-devops" or q.get("tool") in {track, "full-devops"})]
    if not pool: pool = INTERVIEW_DATA["questions"]
    resume_terms = [x for x, _ in Counter(normalize_tokens(resume_text + " " + job_description)).most_common(15)]
    selected = []
    used = set()
    for idx, round_name in enumerate(rounds):
        candidates = [q for q in pool if q["id"] not in used]
        candidates.sort(key=lambda q: (q.get("difficulty") != difficulty, random.random()))
        q = candidates[0]
        used.add(q["id"])
        prompt = q["prompt"]
        if idx == 0:
            prompt = "Give a 90-second introduction focused on the role, your strongest relevant skills, and one truthful achievement."
        elif idx == 1:
            prompt = "Why are you interested in this role, and describe a difficult team situation using the STAR method."
        elif idx == 5:
            prompt = "Write or explain a small automation script that validates a service health endpoint, returns a non-zero exit code on failure, and produces useful logs."
        elif idx == 8:
            prompt = "Summarize why you should be selected, your current limitations, and your first 30-day learning plan."
        if resume_terms and idx in {2, 6}:
            prompt += " Relate your answer to these resume/job terms where truthful: " + ", ".join(resume_terms[:6]) + "."
        selected.append({"id": f"REC-{idx}-{q['id']}", "round": round_name, "prompt": prompt, "keywords": q.get("keywords", []) + resume_terms[:4], "difficulty": difficulty})
    return selected


def start_recruitment(student_id: int, target_role: str, track: str, difficulty: str, resume_text: str = "", job_description: str = "") -> dict[str, Any]:
    target_role = clean_text(target_role, 160) or "DevOps Engineer"
    difficulty = difficulty if difficulty in LEVELS else "Intermediate"
    questions = _recruitment_questions(track, difficulty, resume_text, job_description)
    state = {"index": 0, "questions": questions, "answers": [], "scores": [], "target_role": target_role}
    sid = f"REC-{secrets.token_hex(10)}"; ts = now_iso()
    with db_connect() as conn:
        conn.execute("INSERT INTO recruitment_sessions(id,student_id,target_role,track,difficulty,resume_text,job_description,state_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                     (sid, student_id, target_role, track, difficulty, clean_text(resume_text, 80_000), clean_text(job_description, 80_000), json.dumps(state), ts))
    q = questions[0]
    return {"session_id": sid, "target_role": target_role, "round": q["round"], "question": q, "question_number": 1, "total_questions": len(questions)}


def answer_recruitment(session_id: str, student_id: int, answer: str) -> dict[str, Any]:
    answer = clean_text(answer, 30_000)
    if len(answer) < 15:
        raise ValueError("Provide a complete interview answer.")
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM recruitment_sessions WHERE id=? AND student_id=?", (session_id, student_id)).fetchone()
        if not row or row["status"] != "active":
            raise ValueError("Recruitment session is unavailable.")
        state = json.loads(row["state_json"])
        q = state["questions"][state["index"]]
        score, rubric, missing = _score_rubric(answer, q.get("keywords", []), incident=q["round"] == "Troubleshooting")
        # Behavioral rounds also value structure and specificity.
        if q["round"] in {"Screening", "HR", "Managerial", "Final HR"}:
            text = answer.lower(); structure = 100 if any(x in text for x in ("situation", "task", "action", "result", "because", "outcome")) else 55
            score = round(score * .65 + structure * .35, 1); rubric["behavioral_structure"] = structure
        state["answers"].append({"question": q, "answer": answer, "score": score, "rubric": rubric, "missing": missing})
        state["scores"].append(score); state["index"] += 1
        if state["index"] >= len(state["questions"]):
            final = round(sum(state["scores"]) / len(state["scores"]), 1)
            passed = final >= PASS_MARKS.get(row["difficulty"], 75)
            conn.execute("UPDATE recruitment_sessions SET state_json=?,score=?,passed=?,status='completed',completed_at=? WHERE id=?", (json.dumps(state), final, int(passed), now_iso(), session_id))
            weak = sorted(state["answers"], key=lambda x: x["score"])[:3]
            report = {
                "completed": True, "score": final, "passed": passed, "target_role": row["target_role"],
                "round_scores": [{"round": a["question"]["round"], "score": a["score"]} for a in state["answers"]],
                "weak_rounds": [{"round": a["question"]["round"], "score": a["score"], "missing": a["missing"][:6]} for a in weak],
                "recommendation": "Interview-ready" if passed else "Repeat weak rounds after targeted practice and evidence-based answer revision.",
            }
            return report
        conn.execute("UPDATE recruitment_sessions SET state_json=? WHERE id=?", (json.dumps(state), session_id))
        nxt = state["questions"][state["index"]]
    feedback = "Strong answer." if score >= 80 else ("Acceptable, but make it more specific and evidence-driven." if score >= 65 else "The answer needs clearer technical reasoning, evidence, and outcomes.")
    return {"completed": False, "answer_score": score, "rubric": rubric, "missing": missing, "feedback": feedback,
            "round": nxt["round"], "question": nxt, "question_number": state["index"]+1, "total_questions": len(state["questions"])}


def capstones() -> dict[str, Any]:
    return {"capstones": COMPANY["capstones"]}



def submit_capstone(student_id: int, capstone_id: str, submission: str) -> dict[str, Any]:
    capstone = next((x for x in COMPANY["capstones"] if x["id"] == capstone_id), None)
    if not capstone:
        raise ValueError("Capstone project not found.")
    submission = clean_text(submission, 80000)
    if len(submission) < 250:
        raise ValueError("Capstone submission must include architecture, implementation, security, validation, observability, recovery, and operational handover.")
    keywords = capstone.get("keywords", []) + ["architecture", "security", "validation", "observability", "slo", "rollback", "disaster recovery", "cost", "handover", "documentation"]
    score, rubric, missing = _score_rubric(submission, keywords, incident=True)
    text = submission.lower()
    architecture = 100 if any(x in text for x in ("architecture", "diagram", "design decision", "trade-off")) else 35
    automation = 100 if any(x in text for x in ("pipeline", "automation", "infrastructure as code", "terraform", "ansible")) else 45
    governance = 100 if any(x in text for x in ("approval", "policy", "audit", "compliance", "governance")) else 40
    rubric.update({"architecture": architecture, "automation": automation, "governance": governance})
    score = round(score * .65 + architecture * .15 + automation * .10 + governance * .10, 1)
    passed = score >= 82
    feedback = "Enterprise capstone accepted." if passed else "Capstone requires additional enterprise evidence and operational completeness."
    if missing:
        feedback += " Strengthen: " + ", ".join(missing[:10]) + "."
    run_id = f"CAPRUN-{secrets.token_hex(8)}"; ts = now_iso()
    with db_connect() as conn:
        conn.execute("INSERT INTO capstone_runs(id,student_id,capstone_id,submission,score,rubric_json,status,feedback,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                     (run_id, student_id, capstone_id, submission, score, json.dumps(rubric), "passed" if passed else "needs_review", feedback, ts))
        conn.execute("INSERT INTO audit_log(student_id,action,detail,created_at) VALUES(?,?,?,?)", (student_id, "capstone_submitted", f"{capstone_id};score={score}", ts))
    return {"id": run_id, "capstone": capstone, "score": score, "passed": passed, "rubric": rubric, "missing": missing, "feedback": feedback}

def v2_backup_tables() -> list[str]:
    return ["app_settings", "company_ticket_runs", "incident_runs", "lab_runs", "recruitment_sessions", "capstone_runs", "coaching_notes"]
