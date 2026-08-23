"""Billinger v2.3 Training Institute Edition features.

Standard-library only. Adds institute administration, batches, daily plans,
practical examinations, project workspaces, certificates, verified content
staging, local backups and offline update staging.
"""
from __future__ import annotations

import base64
import csv
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
DATA_DIR = BASE_DIR / "data"
WORKSPACE_DIR = Path(os.environ.get("BILLINGER_WORKSPACE_DIR", str(BASE_DIR / "student_workspaces"))).resolve()
CERT_DIR = Path(os.environ.get("BILLINGER_CERT_DIR", str(BASE_DIR / "certificates"))).resolve()
BACKUP_DIR = Path(os.environ.get("BILLINGER_BACKUP_DIR", str(BASE_DIR / "backups"))).resolve()
IMPORT_DIR = Path(os.environ.get("BILLINGER_IMPORT_DIR", str(BASE_DIR / "imports"))).resolve()
UPDATE_DIR = Path(os.environ.get("BILLINGER_UPDATE_DIR", str(BASE_DIR / "updates"))).resolve()
LEARNING_DIR = BASE_DIR / "learning_resources"
DB_PATH = Path(os.environ.get("BILLINGER_DB_PATH", str(DATA_DIR / "billinger.db"))).resolve()
CATALOG = json.loads((CONTENT_DIR / "devops_catalog.json").read_text(encoding="utf-8"))
COMPANY = json.loads((CONTENT_DIR / "company_scenarios.json").read_text(encoding="utf-8"))
TOOLS = CATALOG["tools"]
TOOL_MAP = {t["slug"]: t for t in TOOLS}
LEVELS = ["Beginner", "Intermediate", "Advanced", "Master"]
PASS_MARKS = {"Beginner": 70, "Intermediate": 75, "Advanced": 80, "Master": 85}
ROLE_TRACKS = [
    "DevOps Trainee", "Junior DevOps Engineer", "DevOps Engineer", "Senior DevOps Engineer",
    "Site Reliability Engineer", "Cloud Engineer", "Platform Engineer", "Build and Release Engineer",
    "Kubernetes Administrator", "Infrastructure Automation Engineer",
]

TOOL_ORDER = [
    "linux", "networking", "git", "shell", "python-automation", "docker", "cicd", "jenkins", "github-actions",
    "kubernetes", "terraform", "ansible", "aws", "azure", "gcp", "observability", "logging",
    "devsecops", "sre", "system-design", "databases",
]
PREREQUISITES = {
    "networking": ["linux"], "git": ["linux"], "shell": ["linux"], "python-automation": ["linux", "git"],
    "docker": ["linux", "networking", "git"], "cicd": ["git", "shell"], "jenkins": ["cicd"],
    "github-actions": ["git", "cicd"], "kubernetes": ["docker", "networking"],
    "terraform": ["linux", "networking", "git"], "ansible": ["linux", "shell"],
    "aws": ["linux", "networking"], "azure": ["linux", "networking"], "gcp": ["linux", "networking"],
    "observability": ["linux", "networking"], "logging": ["linux", "observability"],
    "devsecops": ["git", "cicd", "docker"], "sre": ["observability", "logging", "networking"],
    "system-design": ["kubernetes", "terraform", "observability", "sre"], "databases": ["linux", "networking"],
}

SCHEMA_V23 = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS institute_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    target_role TEXT NOT NULL DEFAULT 'DevOps Engineer',
    level TEXT NOT NULL DEFAULT 'Beginner',
    deadline TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batch_members (
    batch_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    joined_at TEXT NOT NULL,
    PRIMARY KEY(batch_id, student_id),
    FOREIGN KEY(batch_id) REFERENCES batches(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL DEFAULT '',
    due_date TEXT NOT NULL DEFAULT '',
    instructions TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY(batch_id) REFERENCES batches(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(batch_id) REFERENCES batches(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS student_profiles (
    student_id INTEGER PRIMARY KEY,
    target_role TEXT NOT NULL DEFAULT 'DevOps Engineer',
    study_minutes INTEGER NOT NULL DEFAULT 90,
    interview_date TEXT NOT NULL DEFAULT '',
    active_track TEXT NOT NULL DEFAULT 'Full DevOps Track',
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS daily_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    plan_date TEXT NOT NULL,
    items_json TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    UNIQUE(student_id, plan_date),
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS practical_exam_runs (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    exam_code TEXT NOT NULL,
    tool TEXT NOT NULL,
    level TEXT NOT NULL,
    scenario TEXT NOT NULL,
    hidden_checks_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    response TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    report_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS workspace_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    tool TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(student_id, relative_path),
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS certificates (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    certificate_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    score REAL NOT NULL,
    verification_code TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS content_imports (
    id TEXT PRIMARY KEY,
    zip_name TEXT NOT NULL,
    status TEXT NOT NULL,
    staged_path TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS content_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id TEXT NOT NULL,
    title TEXT NOT NULL,
    primary_tool TEXT NOT NULL,
    level TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    source_file TEXT NOT NULL,
    added_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS backup_records (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS update_records (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    detected_version TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    staged_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

DEFAULT_INSTITUTE_SETTINGS = {
    "admin_name": "Institute Administrator",
    "admin_pin_hash": "",
    "auto_backup": True,
    "backup_keep": 10,
    "institute_name": "Billinger DevOps Academy",
}
_ADMIN_TOKENS: dict[str, dt.datetime] = {}
_ADMIN_FAILURES: list[dt.datetime] = []


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        try:
            return bool(super().__exit__(exc_type, exc, tb))
        finally:
            self.close()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return None if row is None else {k: row[k] for k in row.keys()}


def _json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _safe_text(value: Any, max_len: int = 100_000) -> str:
    return str(value or "").replace("\x00", "").strip()[:max_len]


def _hash_pin(pin: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt.encode("ascii"), 180_000).hex()
    return f"{salt}${digest}"


def _verify_pin(pin: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt.encode("ascii"), 180_000).hex()
    return secrets.compare_digest(candidate, digest)


def _setting_get(key: str, default: Any = None) -> Any:
    with _connect() as conn:
        row = conn.execute("SELECT value FROM institute_settings WHERE key=?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except json.JSONDecodeError:
        return row["value"]


def _setting_set(key: str, value: Any) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO institute_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
            (key, _json_value(value), now_iso()),
        )
        conn.commit()


def init_v23_db() -> None:
    for folder in (WORKSPACE_DIR, CERT_DIR, BACKUP_DIR, IMPORT_DIR, UPDATE_DIR):
        folder.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(SCHEMA_V23)
        columns = {r[1] for r in conn.execute("PRAGMA table_info(students)").fetchall()}
        if "active" not in columns:
            conn.execute("ALTER TABLE students ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
        for key, value in DEFAULT_INSTITUTE_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO institute_settings(key,value,updated_at) VALUES(?,?,?)", (key, _json_value(value), now_iso()))
        students = conn.execute("SELECT id FROM students").fetchall()
        for student in students:
            conn.execute(
                "INSERT OR IGNORE INTO student_profiles(student_id,target_role,study_minutes,interview_date,active_track,updated_at) VALUES(?,?,?,?,?,?)",
                (student["id"], "DevOps Engineer", 90, "", "Full DevOps Track", now_iso()),
            )
        conn.commit()


def admin_status() -> dict[str, Any]:
    return {
        "configured": bool(_setting_get("admin_pin_hash", "")),
        "admin_name": _setting_get("admin_name", "Institute Administrator"),
        "institute_name": _setting_get("institute_name", "Billinger DevOps Academy"),
    }


def admin_setup(pin: str, admin_name: str, institute_name: str) -> dict[str, Any]:
    if _setting_get("admin_pin_hash", ""):
        raise ValueError("Administrator access is already configured.")
    if len(pin) < 4 or len(pin) > 30:
        raise ValueError("Administrator PIN must contain 4 to 30 characters.")
    _setting_set("admin_pin_hash", _hash_pin(pin))
    _setting_set("admin_name", _safe_text(admin_name, 120) or "Institute Administrator")
    _setting_set("institute_name", _safe_text(institute_name, 160) or "Billinger DevOps Academy")
    return admin_auth(pin)


def admin_auth(pin: str) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(minutes=15)
    _ADMIN_FAILURES[:] = [stamp for stamp in _ADMIN_FAILURES if stamp >= cutoff]
    if len(_ADMIN_FAILURES) >= 8:
        raise PermissionError("Too many failed administrator sign-in attempts. Try again later.")
    stored = _setting_get("admin_pin_hash", "")
    if not _verify_pin(pin, stored):
        _ADMIN_FAILURES.append(now)
        raise ValueError("Invalid administrator PIN.")
    _ADMIN_FAILURES.clear()
    token = secrets.token_urlsafe(32)
    expires = now + dt.timedelta(hours=8)
    _ADMIN_TOKENS[token] = expires
    return {"authenticated": True, "token": token, "expires_at": expires.isoformat(), **admin_status()}


def require_admin(token: str) -> None:
    expires = _ADMIN_TOKENS.get(token)
    if not expires or expires < dt.datetime.now(dt.timezone.utc):
        _ADMIN_TOKENS.pop(token, None)
        raise PermissionError("Administrator session is missing or expired.")


def save_institute_settings(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("admin_name", "institute_name"):
        if key in data:
            _setting_set(key, _safe_text(data[key], 160))
    if "auto_backup" in data:
        _setting_set("auto_backup", bool(data["auto_backup"]))
    if "backup_keep" in data:
        _setting_set("backup_keep", max(2, min(50, int(data["backup_keep"]))))
    if data.get("new_pin"):
        pin = _safe_text(data["new_pin"], 30)
        if len(pin) < 4:
            raise ValueError("New administrator PIN must contain at least 4 characters.")
        _setting_set("admin_pin_hash", _hash_pin(pin))
        _ADMIN_TOKENS.clear()
    return admin_status() | {"auto_backup": _setting_get("auto_backup", True), "backup_keep": _setting_get("backup_keep", 10)}


def _student_progress(student_id: int) -> dict[str, Any]:
    with _connect() as conn:
        rows = conn.execute("SELECT item_type,status,score FROM progress WHERE student_id=?", (student_id,)).fetchall()
        tests = conn.execute("SELECT COUNT(*) c, COALESCE(AVG(score),0) a FROM test_sessions WHERE student_id=? AND completed_at<>''", (student_id,)).fetchone()
        interviews = conn.execute("SELECT COUNT(*) c, COALESCE(AVG(score),0) a FROM interview_sessions WHERE student_id=? AND status='completed'", (student_id,)).fetchone()
        exams = conn.execute("SELECT COUNT(*) c, COALESCE(AVG(score),0) a FROM practical_exam_runs WHERE student_id=? AND status IN ('passed','needs_review','failed')", (student_id,)).fetchone()
    lessons = sum(1 for r in rows if r["item_type"] == "lesson" and r["status"] == "completed")
    labs = sum(1 for r in rows if r["item_type"] == "lab" and r["status"] == "passed")
    scores = [float(r["score"]) for r in rows if float(r["score"]) > 0]
    return {
        "lessons": lessons, "labs": labs, "tests": int(tests["c"]), "test_average": round(float(tests["a"]), 1),
        "interviews": int(interviews["c"]), "interview_average": round(float(interviews["a"]), 1),
        "practical_exams": int(exams["c"]), "practical_average": round(float(exams["a"]), 1),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
    }


def admin_overview() -> dict[str, Any]:
    with _connect() as conn:
        students = [_row(r) for r in conn.execute("SELECT id,name,email,active,last_active,created_at FROM students ORDER BY name").fetchall()]
        batches = [_row(r) for r in conn.execute("SELECT * FROM batches ORDER BY active DESC,name").fetchall()]
        memberships = conn.execute("SELECT batch_id,student_id FROM batch_members ORDER BY batch_id,student_id").fetchall()
        assignments = [_row(r) for r in conn.execute("SELECT * FROM assignments ORDER BY created_at DESC LIMIT 100").fetchall()]
        announcements = [_row(r) for r in conn.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 50").fetchall()]
        imports = [_row(r) for r in conn.execute("SELECT id,zip_name,status,created_at,published_at,manifest_json FROM content_imports ORDER BY created_at DESC").fetchall()]
    member_ids: dict[int, list[int]] = defaultdict(list)
    for membership in memberships:
        member_ids[int(membership["batch_id"])].append(int(membership["student_id"]))
    for batch in batches:
        batch["member_ids"] = member_ids.get(int(batch["id"]), [])
        batch["member_count"] = len(batch["member_ids"])
    for student in students:
        student["progress"] = _student_progress(int(student["id"]))
    for item in imports:
        manifest = json.loads(item.pop("manifest_json") or "{}")
        item["document_count"] = len(manifest.get("documents", []))
    return {
        "status": admin_status(), "students": students, "batches": batches, "assignments": assignments,
        "announcements": announcements, "imports": imports, "role_tracks": ROLE_TRACKS, "levels": LEVELS,
        "summary": {
            "active_students": sum(1 for s in students if s.get("active")), "batches": len(batches),
            "active_assignments": sum(1 for a in assignments if a.get("status") == "active"),
            "published_imports": sum(1 for i in imports if i.get("status") == "published"),
        },
    }


def save_batch(data: dict[str, Any]) -> dict[str, Any]:
    name = _safe_text(data.get("name"), 120)
    if len(name) < 2:
        raise ValueError("Batch name is required.")
    level = _safe_text(data.get("level"), 30) or "Beginner"
    role = _safe_text(data.get("target_role"), 120) or "DevOps Engineer"
    if level not in LEVELS or role not in ROLE_TRACKS:
        raise ValueError("Invalid batch level or target role.")
    batch_id = int(data.get("id") or 0)
    values = (name, _safe_text(data.get("description"), 1000), role, level, _safe_text(data.get("deadline"), 20), 1 if data.get("active", True) else 0, now_iso())
    with _connect() as conn:
        if batch_id:
            conn.execute("UPDATE batches SET name=?,description=?,target_role=?,level=?,deadline=?,active=?,updated_at=? WHERE id=?", values + (batch_id,))
        else:
            cur = conn.execute("INSERT INTO batches(name,description,target_role,level,deadline,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", values[:-1] + (values[-1], values[-1]))
            batch_id = int(cur.lastrowid)
        conn.commit()
        row = conn.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
    return _row(row) or {}


def assign_batch_member(batch_id: int, student_id: int, assigned: bool = True) -> dict[str, Any]:
    with _connect() as conn:
        if assigned:
            conn.execute("INSERT OR IGNORE INTO batch_members(batch_id,student_id,joined_at) VALUES(?,?,?)", (batch_id, student_id, now_iso()))
        else:
            conn.execute("DELETE FROM batch_members WHERE batch_id=? AND student_id=?", (batch_id, student_id))
        conn.commit()
    return {"saved": True}


def update_student(data: dict[str, Any]) -> dict[str, Any]:
    student_id = int(data.get("student_id") or 0)
    if not student_id:
        raise ValueError("Student is required.")
    name = _safe_text(data.get("name"), 120)
    email = _safe_text(data.get("email"), 200)
    active = 1 if data.get("active", True) else 0
    role = _safe_text(data.get("target_role"), 120) or "DevOps Engineer"
    minutes = max(20, min(480, int(data.get("study_minutes") or 90)))
    if role not in ROLE_TRACKS:
        raise ValueError("Invalid target role.")
    with _connect() as conn:
        if name:
            conn.execute("UPDATE students SET name=?,email=?,active=? WHERE id=?", (name, email, active, student_id))
        conn.execute(
            "INSERT INTO student_profiles(student_id,target_role,study_minutes,interview_date,active_track,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(student_id) DO UPDATE SET target_role=excluded.target_role,study_minutes=excluded.study_minutes,interview_date=excluded.interview_date,active_track=excluded.active_track,updated_at=excluded.updated_at",
            (student_id, role, minutes, _safe_text(data.get("interview_date"), 20), _safe_text(data.get("active_track"), 120) or "Full DevOps Track", now_iso()),
        )
        if data.get("reset_pin"):
            conn.execute("UPDATE students SET pin_hash='' WHERE id=?", (student_id,))
        conn.commit()
    return {"saved": True}


def create_assignment(data: dict[str, Any]) -> dict[str, Any]:
    batch_id = int(data.get("batch_id") or 0)
    title = _safe_text(data.get("title"), 180)
    if not batch_id or len(title) < 3:
        raise ValueError("Batch and assignment title are required.")
    item_type = _safe_text(data.get("item_type"), 40) or "custom"
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO assignments(batch_id,title,item_type,item_id,due_date,instructions,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (batch_id, title, item_type, _safe_text(data.get("item_id"), 120), _safe_text(data.get("due_date"), 20), _safe_text(data.get("instructions"), 4000), "active", now_iso()),
        )
        conn.commit()
    return {"id": cur.lastrowid, "saved": True}


def create_announcement(data: dict[str, Any]) -> dict[str, Any]:
    batch_id = int(data.get("batch_id") or 0)
    title = _safe_text(data.get("title"), 180)
    message = _safe_text(data.get("message"), 5000)
    if not batch_id or not title or not message:
        raise ValueError("Batch, title and announcement message are required.")
    with _connect() as conn:
        cur = conn.execute("INSERT INTO announcements(batch_id,title,message,created_at) VALUES(?,?,?,?)", (batch_id, title, message, now_iso()))
        conn.commit()
    return {"id": cur.lastrowid, "saved": True}


def _tool_completion(student_id: int) -> dict[str, float]:
    lesson_ids: dict[str, set[str]] = defaultdict(set)
    for tool in TOOLS:
        for level in tool["levels"]:
            for lesson in level["lessons"]:
                lesson_ids[tool["slug"]].add(lesson["id"])
    with _connect() as conn:
        completed = {r["item_id"] for r in conn.execute("SELECT item_id FROM progress WHERE student_id=? AND item_type='lesson' AND status='completed'", (student_id,)).fetchall()}
    return {slug: round(len(ids & completed) / max(1, len(ids)) * 100, 1) for slug, ids in lesson_ids.items()}


def dependency_roadmap(student_id: int) -> dict[str, Any]:
    completion = _tool_completion(student_id)
    items = []
    for slug in TOOL_ORDER:
        prereqs = PREREQUISITES.get(slug, [])
        missing = [p for p in prereqs if completion.get(p, 0) < 60]
        pct = completion.get(slug, 0)
        status = "completed" if pct >= 95 else "available" if not missing else "locked"
        items.append({
            "slug": slug, "name": TOOL_MAP[slug]["name"], "icon": TOOL_MAP[slug]["icon"], "completion": pct,
            "prerequisites": prereqs, "missing_prerequisites": missing, "status": status,
        })
    return {"items": items}


def _weak_tools(student_id: int) -> list[str]:
    completion = _tool_completion(student_id)
    with _connect() as conn:
        scores = defaultdict(list)
        for row in conn.execute("SELECT item_id,score FROM progress WHERE student_id=? AND score>0", (student_id,)).fetchall():
            item = row["item_id"]
            for tool in TOOLS:
                if item.startswith(tool["slug"] + "-"):
                    scores[tool["slug"]].append(float(row["score"]))
                    break
    ranked = []
    for slug in TOOL_ORDER:
        average = sum(scores[slug]) / len(scores[slug]) if scores[slug] else 50
        weakness = (100 - completion.get(slug, 0)) * 0.65 + (100 - average) * 0.35
        ranked.append((weakness, slug))
    return [slug for _, slug in sorted(ranked, reverse=True)]


def generate_daily_plan(student_id: int, plan_date: str = "") -> dict[str, Any]:
    day = plan_date or dt.date.today().isoformat()
    with _connect() as conn:
        profile = conn.execute("SELECT * FROM student_profiles WHERE student_id=?", (student_id,)).fetchone()
    minutes = int(profile["study_minutes"] if profile else 90)
    target_role = profile["target_role"] if profile else "DevOps Engineer"
    weak = _weak_tools(student_id)
    roadmap = dependency_roadmap(student_id)["items"]
    available = [x["slug"] for x in roadmap if x["status"] != "locked" and x["completion"] < 95]
    focus = next((x for x in weak if x in available), available[0] if available else "sre")
    secondary = next((x for x in weak if x != focus and x in available), focus)
    labels = [
        ("lesson", focus, "Read one focused lesson and the assigned course-book section"),
        ("practice", focus, "Complete one company-style practice task with evidence and rollback"),
        ("test", focus, "Take a short mastery check and review every incorrect answer"),
        ("revision", secondary, "Revise a weak topic using spaced-repetition notes"),
        ("interview", focus, f"Answer one {target_role} interview scenario aloud"),
    ]
    weights = [.28, .27, .17, .13, .15]
    durations = [max(3, round(minutes * weight)) for weight in weights]
    durations[-1] += minutes - sum(durations)
    if durations[-1] < 3:
        deficit = 3 - durations[-1]
        durations[-1] = 3
        for i in range(4):
            take = min(deficit, max(0, durations[i] - 3))
            durations[i] -= take; deficit -= take
            if deficit == 0: break
    chunks = [(kind, tool, title, durations[i]) for i, (kind, tool, title) in enumerate(labels)]
    items = [{"order": i + 1, "type": kind, "tool": tool, "tool_name": TOOL_MAP[tool]["name"], "title": title, "minutes": duration, "completed": False} for i, (kind, tool, title, duration) in enumerate(chunks)]
    with _connect() as conn:
        conn.execute(
            "INSERT INTO daily_plans(student_id,plan_date,items_json,generated_at) VALUES(?,?,?,?) ON CONFLICT(student_id,plan_date) DO UPDATE SET items_json=excluded.items_json,generated_at=excluded.generated_at",
            (student_id, day, _json_value(items), now_iso()),
        )
        conn.commit()
    return {"date": day, "study_minutes": sum(x["minutes"] for x in items), "target_role": target_role, "focus_tool": focus, "items": items}


def student_hub(student_id: int) -> dict[str, Any]:
    with _connect() as conn:
        profile = _row(conn.execute("SELECT * FROM student_profiles WHERE student_id=?", (student_id,)).fetchone()) or {}
        batches = [_row(r) for r in conn.execute("SELECT b.* FROM batches b JOIN batch_members m ON m.batch_id=b.id WHERE m.student_id=? AND b.active=1 ORDER BY b.name", (student_id,)).fetchall()]
        batch_ids = [b["id"] for b in batches]
        if batch_ids:
            placeholders = ",".join("?" for _ in batch_ids)
            assignments = [_row(r) for r in conn.execute(f"SELECT * FROM assignments WHERE batch_id IN ({placeholders}) AND status='active' ORDER BY due_date,created_at DESC", batch_ids).fetchall()]
            announcements = [_row(r) for r in conn.execute(f"SELECT * FROM announcements WHERE batch_id IN ({placeholders}) ORDER BY created_at DESC LIMIT 20", batch_ids).fetchall()]
        else:
            assignments, announcements = [], []
        certificates = [_row(r) for r in conn.execute("SELECT * FROM certificates WHERE student_id=? ORDER BY created_at DESC", (student_id,)).fetchall()]
    return {
        "profile": profile, "batches": batches, "assignments": assignments, "announcements": announcements,
        "roadmap": dependency_roadmap(student_id), "today": generate_daily_plan(student_id), "certificates": certificates,
        "role_tracks": ROLE_TRACKS,
    }


def practical_exam_templates(tool: str = "", level: str = "") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for t in TOOLS:
        if tool and t["slug"] != tool:
            continue
        for lev in t["levels"]:
            if level and lev["name"] != level:
                continue
            lab = lev["labs"][0]
            items.append({
                "exam_code": f"PEX-{t['slug'].upper()}-{lev['name'][0]}", "tool": t["slug"], "tool_name": t["name"], "icon": t["icon"],
                "level": lev["name"], "title": f"{t['name']} {lev['name']} Practical", "scenario": lab["scenario"],
                "duration_minutes": {"Beginner": 30, "Intermediate": 45, "Advanced": 60, "Master": 90}[lev["name"]],
                "requirements": ["Document diagnosis and assumptions", "Provide commands or configuration", "Show validation evidence", "Include security controls", "Include rollback or recovery"],
            })
    return items


def _exam_source(exam_code: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for t in TOOLS:
        for lev in t["levels"]:
            code = f"PEX-{t['slug'].upper()}-{lev['name'][0]}"
            if code == exam_code:
                return t, lev
    raise ValueError("Practical examination was not found.")


def start_practical_exam(student_id: int, exam_code: str) -> dict[str, Any]:
    tool, level = _exam_source(exam_code)
    lab = level["labs"][0]
    duration = {"Beginner": 30, "Intermediate": 45, "Advanced": 60, "Master": 90}[level["name"]]
    run_id = "pex_" + secrets.token_hex(10)
    started = dt.datetime.now(dt.timezone.utc)
    expires = started + dt.timedelta(minutes=duration)
    hidden = list(dict.fromkeys(lab.get("keywords", []) + ["validate", "evidence", "security", "rollback"]))
    with _connect() as conn:
        conn.execute(
            "INSERT INTO practical_exam_runs(id,student_id,exam_code,tool,level,scenario,hidden_checks_json,started_at,expires_at,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (run_id, student_id, exam_code, tool["slug"], level["name"], lab["scenario"], _json_value(hidden), started.isoformat(), expires.isoformat(), "active"),
        )
        conn.commit()
    return {"run_id": run_id, "exam_code": exam_code, "tool": tool["slug"], "tool_name": tool["name"], "level": level["name"], "title": f"{tool['name']} {level['name']} Practical", "scenario": lab["scenario"], "duration_minutes": duration, "started_at": started.isoformat(), "expires_at": expires.isoformat(), "visible_requirements": ["Explain diagnosis", "Show implementation", "Provide validation evidence", "Address security", "Prepare rollback"]}


def submit_practical_exam(run_id: str, student_id: int, response: str) -> dict[str, Any]:
    response = _safe_text(response, 60_000)
    if len(response.split()) < 60:
        raise ValueError("Practical response is too short. Include diagnosis, implementation, evidence, security and rollback.")
    with _connect() as conn:
        row = conn.execute("SELECT * FROM practical_exam_runs WHERE id=? AND student_id=?", (run_id, student_id)).fetchone()
    if not row or row["status"] != "active":
        raise ValueError("Practical examination session is unavailable or already completed.")
    hidden = json.loads(row["hidden_checks_json"])
    text = response.lower()
    matched = [x for x in hidden if x.lower() in text]
    coverage = len(matched) / max(1, len(hidden)) * 100
    rubric = {
        "technical": min(100, coverage * .85 + min(15, len(response.split()) / 12)),
        "diagnosis": 100 if any(x in text for x in ("hypothesis", "root cause", "diagnos", "inspect")) else 45,
        "evidence": 100 if any(x in text for x in ("evidence", "output", "log", "metric", "test result")) else 35,
        "security": 100 if any(x in text for x in ("least privilege", "secret", "permission", "security", "scan")) else 40,
        "rollback": 100 if any(x in text for x in ("rollback", "restore", "revert", "backup", "snapshot")) else 30,
        "communication": 100 if any(x in text for x in ("stakeholder", "status update", "manager", "approval", "incident channel")) else 45,
    }
    weights = {"technical": .35, "diagnosis": .17, "evidence": .16, "security": .11, "rollback": .13, "communication": .08}
    score = round(sum(rubric[k] * weights[k] for k in weights), 1)
    expired = dt.datetime.now(dt.timezone.utc) > dt.datetime.fromisoformat(row["expires_at"])
    if expired:
        score = max(0, score - 10)
    passed = score >= PASS_MARKS.get(row["level"], 75)
    missing = [x for x in hidden if x not in matched][:12]
    report = {"rubric": {k: round(v, 1) for k, v in rubric.items()}, "matched_checks": matched, "missing_checks": missing, "expired": expired}
    status = "passed" if passed else "needs_review"
    with _connect() as conn:
        conn.execute("UPDATE practical_exam_runs SET completed_at=?,status=?,response=?,score=?,report_json=? WHERE id=?", (now_iso(), status, response, score, _json_value(report), run_id))
        conn.execute(
            "INSERT INTO progress(student_id,item_type,item_id,status,score,attempts,notes,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(student_id,item_type,item_id) DO UPDATE SET status=excluded.status,score=excluded.score,attempts=progress.attempts+1,notes=excluded.notes,updated_at=excluded.updated_at",
            (student_id, "practical_exam", row["exam_code"], status, score, 1, "Practical exam evaluated", now_iso()),
        )
        conn.commit()
    return {"score": score, "passed": passed, "status": status, **report}


def _workspace_root(student_id: int) -> Path:
    root = (WORKSPACE_DIR / f"student_{student_id:02d}").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_workspace_path(student_id: int, relative_path: str) -> Path:
    rel = PurePosixPath(_safe_text(relative_path, 240).replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("Invalid workspace path.")
    root = _workspace_root(student_id)
    path = (root / Path(*rel.parts)).resolve()
    if root != path and root not in path.parents:
        raise ValueError("Workspace path is outside the student directory.")
    return path


def list_workspace(student_id: int) -> dict[str, Any]:
    root = _workspace_root(student_id)
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            files.append({"path": rel, "size_bytes": path.stat().st_size, "modified_at": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(), "text_editable": path.suffix.lower() in {".txt", ".md", ".yaml", ".yml", ".json", ".py", ".sh", ".tf", ".ini", ".cfg", ".dockerfile"} or path.name.lower() in {"dockerfile", "jenkinsfile"}})
    return {"root": root.name, "files": files, "total_bytes": sum(x["size_bytes"] for x in files)}


def save_workspace_file(student_id: int, relative_path: str, content: str, tool: str = "general") -> dict[str, Any]:
    path = _safe_workspace_path(student_id, relative_path)
    raw = _safe_text(content, 2_000_000).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO workspace_files(student_id,tool,relative_path,size_bytes,sha256,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(student_id,relative_path) DO UPDATE SET tool=excluded.tool,size_bytes=excluded.size_bytes,sha256=excluded.sha256,updated_at=excluded.updated_at",
            (student_id, tool if tool in TOOL_MAP else "general", path.relative_to(_workspace_root(student_id)).as_posix(), len(raw), digest, now_iso(), now_iso()),
        )
        conn.commit()
    return {"saved": True, "path": path.relative_to(_workspace_root(student_id)).as_posix(), "size_bytes": len(raw), "sha256": digest}


def upload_workspace_file(student_id: int, relative_path: str, content_base64: str, tool: str = "general") -> dict[str, Any]:
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except Exception as exc:
        raise ValueError("Invalid workspace upload encoding.") from exc
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("Workspace upload exceeds the 8 MB limit.")
    path = _safe_workspace_path(student_id, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO workspace_files(student_id,tool,relative_path,size_bytes,sha256,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(student_id,relative_path) DO UPDATE SET tool=excluded.tool,size_bytes=excluded.size_bytes,sha256=excluded.sha256,updated_at=excluded.updated_at",
            (student_id, tool if tool in TOOL_MAP else "general", path.relative_to(_workspace_root(student_id)).as_posix(), len(raw), digest, now_iso(), now_iso()),
        )
        conn.commit()
    return {"saved": True, "path": path.relative_to(_workspace_root(student_id)).as_posix(), "size_bytes": len(raw), "sha256": digest}


def read_workspace_file(student_id: int, relative_path: str) -> tuple[Path, bytes]:
    path = _safe_workspace_path(student_id, relative_path)
    if not path.is_file():
        raise ValueError("Workspace file was not found.")
    return path, path.read_bytes()


def issue_certificate(student_id: int, certificate_type: str, subject: str, score: float) -> dict[str, Any]:
    certificate_type = _safe_text(certificate_type, 80) or "Completion"
    subject = _safe_text(subject, 180)
    if not subject:
        raise ValueError("Certificate subject is required.")
    with _connect() as conn:
        student = conn.execute("SELECT name FROM students WHERE id=?", (student_id,)).fetchone()
    if not student:
        raise ValueError("Student was not found.")
    cid = "cert_" + secrets.token_hex(10)
    verification = "BLG-" + secrets.token_hex(5).upper()
    file_name = f"{verification}.html"
    created = dt.date.today().strftime("%d %B %Y")
    body = f"""<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(subject)} Certificate</title><style>
body{{margin:0;background:#07111f;font-family:Segoe UI,Arial;color:#eaf8ff;display:grid;place-items:center;min-height:100vh}}.cert{{width:1000px;max-width:92vw;padding:65px;border:2px solid #69e7ff;border-radius:28px;background:radial-gradient(circle at top right,#1a2c56,#081421 55%);box-shadow:0 35px 100px #0008;text-align:center;position:relative}}.cert:before{{content:'';position:absolute;inset:16px;border:1px solid #ffffff28;border-radius:20px}}h1{{font-size:54px;margin:20px}}h2{{font-size:36px;color:#69e7ff}}p{{font-size:20px;line-height:1.7}}.code{{font:18px Consolas;background:#0005;padding:12px 18px;border-radius:12px;display:inline-block}}.seal{{width:120px;height:120px;border-radius:50%;display:grid;place-items:center;margin:auto;background:linear-gradient(135deg,#69e7ff,#ad8cff);color:#07111f;font-size:44px;font-weight:900;box-shadow:0 0 45px #69e7ff66}}@media print{{body{{background:white}}.cert{{box-shadow:none;color:#102030}}}}</style></head><body><section class='cert'><div class='seal'>B</div><p>BILLINGER DEVOPS ACADEMY</p><h1>Certificate of {html.escape(certificate_type)}</h1><p>This certifies that</p><h2>{html.escape(student['name'])}</h2><p>has successfully completed <strong>{html.escape(subject)}</strong><br>with a verified score of <strong>{score:.1f}%</strong>.</p><p>{created}</p><div class='code'>Verification: {verification}</div></section></body></html>"""
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    (CERT_DIR / file_name).write_text(body, encoding="utf-8")
    with _connect() as conn:
        conn.execute("INSERT INTO certificates(id,student_id,certificate_type,subject,score,verification_code,file_name,created_at) VALUES(?,?,?,?,?,?,?,?)", (cid, student_id, certificate_type, subject, score, verification, file_name, now_iso()))
        conn.commit()
    return {"id": cid, "verification_code": verification, "file_name": file_name, "download": f"/api/v3/certificate/file?id={cid}"}


def list_certificates(student_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        return [_row(r) for r in conn.execute("SELECT * FROM certificates WHERE student_id=? ORDER BY created_at DESC", (student_id,)).fetchall()]


def certificate_file(certificate_id: str) -> tuple[str, bytes]:
    with _connect() as conn:
        row = conn.execute("SELECT file_name FROM certificates WHERE id=?", (certificate_id,)).fetchone()
    if not row:
        raise ValueError("Certificate was not found.")
    path = (CERT_DIR / row["file_name"]).resolve()
    if CERT_DIR.resolve() not in path.parents or not path.is_file():
        raise ValueError("Certificate file is unavailable.")
    return row["file_name"], path.read_bytes()


def verify_certificate(code: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT c.*,s.name student_name FROM certificates c JOIN students s ON s.id=c.student_id WHERE verification_code=?", (_safe_text(code, 40).upper(),)).fetchone()
    return {"valid": bool(row), "certificate": _row(row)}


def _zip_add_tree(zf: zipfile.ZipFile, folder: Path, prefix: str) -> None:
    if not folder.exists():
        return
    for path in folder.rglob("*"):
        if path.is_file():
            zf.write(path, f"{prefix}/{path.relative_to(folder).as_posix()}")


def create_backup() -> dict[str, Any]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_id = "backup_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + secrets.token_hex(3)
    file_name = backup_id + ".zip"
    target = BACKUP_DIR / file_name
    with tempfile.TemporaryDirectory() as td:
        db_copy = Path(td) / "billinger.db"
        source = _connect()
        dest = sqlite3.connect(db_copy)
        try:
            source.backup(dest)
        finally:
            source.close(); dest.close()
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            zf.write(db_copy, "data/billinger.db")
            _zip_add_tree(zf, WORKSPACE_DIR, "student_workspaces")
            _zip_add_tree(zf, CERT_DIR, "certificates")
            _zip_add_tree(zf, BASE_DIR / "resumes", "resumes")
            _zip_add_tree(zf, BASE_DIR / "labs", "labs")
            zf.writestr("BACKUP_INFO.json", _json_value({"version": "2.9.0", "created_at": now_iso(), "database": "data/billinger.db"}))
    raw = target.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with _connect() as conn:
        conn.execute("INSERT INTO backup_records(id,file_name,size_bytes,sha256,created_at) VALUES(?,?,?,?,?)", (backup_id, file_name, len(raw), digest, now_iso()))
        conn.commit()
    keep = int(_setting_get("backup_keep", 10) or 10)
    _prune_backups(keep)
    return {"id": backup_id, "file_name": file_name, "size_bytes": len(raw), "sha256": digest, "download": f"/api/v3/backup/file?id={backup_id}"}


def _prune_backups(keep: int) -> None:
    with _connect() as conn:
        rows = conn.execute("SELECT id,file_name FROM backup_records ORDER BY created_at DESC").fetchall()
        for row in rows[keep:]:
            (BACKUP_DIR / row["file_name"]).unlink(missing_ok=True)
            conn.execute("DELETE FROM backup_records WHERE id=?", (row["id"],))
        conn.commit()


def list_backups() -> list[dict[str, Any]]:
    with _connect() as conn:
        return [_row(r) for r in conn.execute("SELECT * FROM backup_records ORDER BY created_at DESC").fetchall()]


def backup_file(backup_id: str) -> tuple[str, bytes]:
    with _connect() as conn:
        row = conn.execute("SELECT file_name FROM backup_records WHERE id=?", (backup_id,)).fetchone()
    if not row:
        raise ValueError("Backup was not found.")
    path = (BACKUP_DIR / row["file_name"]).resolve()
    if BACKUP_DIR.resolve() not in path.parents or not path.is_file():
        raise ValueError("Backup file is unavailable.")
    return row["file_name"], path.read_bytes()


def stage_restore(zip_name: str, content_base64: str) -> dict[str, Any]:
    raw = base64.b64decode(content_base64, validate=True)
    if len(raw) > 2 * 1024 * 1024 * 1024:
        raise ValueError("Backup exceeds the 2 GB restore limit.")
    restore_dir = UPDATE_DIR / "pending_restore"
    restore_dir.mkdir(parents=True, exist_ok=True)
    target = restore_dir / "restore.zip"
    target.write_bytes(raw)
    try:
        with zipfile.ZipFile(target) as zf:
            _validate_zip_members(zf, max_files=10000, max_total=5 * 1024 * 1024 * 1024, max_member=4 * 1024 * 1024 * 1024)
            names = set(zf.namelist())
            if "data/billinger.db" not in names or "BACKUP_INFO.json" not in names:
                raise ValueError("This is not a valid Billinger backup package.")
    except zipfile.BadZipFile as exc:
        target.unlink(missing_ok=True)
        raise ValueError("Backup ZIP is invalid.") from exc
    except ValueError:
        target.unlink(missing_ok=True)
        raise
    pending = {"zip_name": _safe_text(zip_name, 240), "path": str(target), "sha256": hashlib.sha256(raw).hexdigest(), "staged_at": now_iso()}
    (restore_dir / "pending.json").write_text(_json_value(pending), encoding="utf-8")
    return {"staged": True, "message": "Restore staged. Close the bot and run Apply_Pending_Restore.bat."}


def _extract_docx_text(raw: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            xml = zf.read("word/document.xml")
    except Exception:
        return ""
    root = ET.fromstring(xml)
    texts: list[str] = []
    for node in root.iter():
        if node.tag.endswith("}t") and node.text:
            texts.append(node.text)
        elif node.tag.endswith("}p"):
            texts.append("\n")
    return " ".join(texts).replace(" \n ", "\n").strip()


def _classify_document(name: str, text: str) -> tuple[str, float, list[tuple[str, int]]]:
    sample = (name + " " + text[:120_000]).lower()
    aliases = {
        "linux": ["linux", "systemd", "filesystem", "bash administration"],
        "networking": ["networking", "dns", "http", "tcp", "routing", "subnet"],
        "git": ["git ", "github repository", "branching", "pull request", "version control"],
        "shell": ["shell scripting", "bash script", "powershell"],
        "python": ["python automation", "python for devops", "pytest"],
        "docker": ["docker", "container", "dockerfile", "containerd"],
        "kubernetes": ["kubernetes", "kubectl", "helm", "pod", "cluster"],
        "cicd": ["ci/cd", "continuous integration", "continuous delivery", "pipeline"],
        "jenkins": ["jenkins", "jenkinsfile"],
        "github-actions": ["github actions", "workflow yaml", "actions runner"],
        "terraform": ["terraform", "infrastructure as code", "hcl"],
        "ansible": ["ansible", "playbook", "inventory"],
        "aws": ["aws", "amazon web services", "ec2", "iam", "cloudformation"],
        "azure": ["azure", "microsoft cloud", "azure devops"],
        "gcp": ["google cloud", "gcp", "gke", "cloud run"],
        "observability": ["prometheus", "grafana", "observability", "metrics", "alerting"],
        "logging": ["elk", "elasticsearch", "opensearch", "logstash", "centralized logging"],
        "devsecops": ["devsecops", "supply chain security", "sast", "dast", "sbom", "vulnerability"],
        "sre": ["site reliability", "sre", "slo", "error budget", "incident management"],
        "system-design": ["system design", "platform engineering", "architecture", "multi-region"],
        "databases": ["database", "postgresql", "mysql", "sql", "backup restore"],
    }
    scores: list[tuple[str, int]] = []
    for slug, terms in aliases.items():
        score = 0
        for term in terms:
            score += sample.count(term) * (6 if term in name.lower() else 1)
        scores.append((slug, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    best, score = scores[0]
    confidence = min(99.0, 45 + score * 2.5) if score else 20.0
    return best, round(confidence, 1), scores[:5]


def _safe_zip_name(name: str) -> str:
    p = PurePosixPath(name.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("ZIP contains an unsafe path.")
    return p.as_posix()


def _validate_zip_members(
    zf: zipfile.ZipFile,
    *,
    max_files: int,
    max_total: int,
    max_member: int,
    max_ratio: float = 200.0,
) -> list[zipfile.ZipInfo]:
    infos = zf.infolist()
    if not infos:
        raise ValueError("ZIP archive is empty.")
    if len(infos) > max_files:
        raise ValueError("ZIP contains too many files.")
    total = 0
    for info in infos:
        _safe_zip_name(info.filename)
        if "\x00" in info.filename:
            raise ValueError("ZIP contains an invalid file name.")
        mode = (info.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise ValueError("ZIP symbolic links are not permitted.")
        if info.flag_bits & 0x1:
            raise ValueError("Encrypted ZIP entries are not permitted.")
        if info.is_dir():
            continue
        if info.file_size < 0 or info.file_size > max_member:
            raise ValueError(f"ZIP member is too large: {info.filename}")
        total += info.file_size
        if total > max_total:
            raise ValueError("Expanded ZIP exceeds the allowed size.")
        if info.file_size > 1024 * 1024:
            ratio = info.file_size / max(1, info.compress_size)
            if ratio > max_ratio:
                raise ValueError(f"ZIP member has an unsafe compression ratio: {info.filename}")
    bad = zf.testzip()
    if bad:
        raise ValueError(f"ZIP integrity check failed at: {bad}")
    return infos


def stage_content_import(zip_name: str, content_base64: str) -> dict[str, Any]:
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except Exception as exc:
        raise ValueError("Invalid ZIP encoding.") from exc
    if len(raw) > 75 * 1024 * 1024:
        raise ValueError("Learning ZIP exceeds the 75 MB browser-import limit. Split it into smaller ZIP files.")
    import_id = "imp_" + secrets.token_hex(8)
    stage = IMPORT_DIR / import_id
    stage.mkdir(parents=True, exist_ok=True)
    archive = stage / "source.zip"
    archive.write_bytes(raw)
    try:
        with zipfile.ZipFile(archive) as zf:
            _validate_zip_members(zf, max_files=600, max_total=600 * 1024 * 1024, max_member=80 * 1024 * 1024)
            groups: dict[str, dict[str, Any]] = {}
            for info in zf.infolist():
                if info.is_dir():
                    continue
                safe = _safe_zip_name(info.filename)
                ext = Path(safe).suffix.lower()
                if ext not in {".pdf", ".docx", ".txt", ".md", ".html", ".htm"}:
                    continue
                if info.file_size > 80 * 1024 * 1024:
                    raise ValueError(f"File is too large: {safe}")
                data = zf.read(info)
                out = stage / "files" / Path(safe).name
                out.parent.mkdir(parents=True, exist_ok=True)
                candidate = out
                n = 2
                while candidate.exists():
                    candidate = out.with_name(f"{out.stem}_{n}{out.suffix}"); n += 1
                candidate.write_bytes(data)
                key = re.sub(r"\.(pdf|docx|txt|md|html?)$", "", Path(safe).name, flags=re.I)
                key = re.sub(r"[_\-]+", " ", key).strip().lower()
                group = groups.setdefault(key, {"display_name": Path(safe).stem, "files": {}, "text": ""})
                group["files"][ext.lstrip(".")] = candidate.name
                if ext == ".docx":
                    group["text"] += "\n" + _extract_docx_text(data)
                elif ext in {".txt", ".md", ".html", ".htm"}:
                    group["text"] += "\n" + data.decode("utf-8", errors="ignore")
            documents = []
            for key, group in groups.items():
                tool, confidence, alternatives = _classify_document(group["display_name"], group["text"])
                words = len(re.findall(r"\w+", group["text"]))
                documents.append({
                    "key": key, "title": group["display_name"], "files": group["files"], "recommended_tool": tool,
                    "recommended_tool_name": TOOL_MAP[tool]["name"], "confidence": confidence,
                    "alternatives": [{"tool": x, "name": TOOL_MAP[x]["name"], "score": s} for x, s in alternatives],
                    "recommended_level": "Beginner" if words < 8000 else "Intermediate" if words < 20000 else "Advanced",
                    "word_count": words, "status": "awaiting_admin_approval",
                })
            if not documents:
                raise ValueError("No supported PDF, DOCX or text learning documents were found in the ZIP.")
    except zipfile.BadZipFile as exc:
        shutil.rmtree(stage, ignore_errors=True)
        raise ValueError("Uploaded file is not a valid ZIP archive.") from exc
    except ValueError:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    manifest = {"import_id": import_id, "zip_name": _safe_text(zip_name, 240), "documents": documents, "tool_options": [{"slug": t["slug"], "name": t["name"]} for t in TOOLS], "levels": LEVELS, "notice": "Recommendations are not published automatically. An administrator must confirm one primary tool and one level per document."}
    (stage / "manifest.json").write_text(_json_value(manifest), encoding="utf-8")
    with _connect() as conn:
        conn.execute("INSERT INTO content_imports(id,zip_name,status,staged_path,manifest_json,created_at) VALUES(?,?,?,?,?,?)", (import_id, _safe_text(zip_name, 240), "awaiting_approval", str(stage), _json_value(manifest), now_iso()))
        conn.commit()
    return manifest


def get_content_import(import_id: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT manifest_json,status,published_at FROM content_imports WHERE id=?", (import_id,)).fetchone()
    if not row:
        raise ValueError("Content import was not found.")
    manifest = json.loads(row["manifest_json"])
    manifest["status"] = row["status"]
    manifest["published_at"] = row["published_at"]
    return manifest


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:70]
    return slug or "resource"


def _chunk_pages(text: str, words_per_page: int = 850) -> list[dict[str, Any]]:
    words = text.split()
    if not words:
        return [{"page": 1, "text": "Text extraction is unavailable. Open the original PDF or DOCX file."}]
    pages = []
    for start in range(0, len(words), words_per_page):
        pages.append({"page": len(pages) + 1, "text": " ".join(words[start:start + words_per_page])})
    return pages


def publish_content_import(import_id: str, mappings: list[dict[str, Any]]) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM content_imports WHERE id=?", (import_id,)).fetchone()
    if not row:
        raise ValueError("Content import was not found.")
    if row["status"] == "published":
        raise ValueError("This import has already been published.")
    manifest = json.loads(row["manifest_json"])
    mapping_by_key = {str(x.get("key")): x for x in mappings if x.get("publish", True)}
    stage = Path(row["staged_path"])
    index_path = LEARNING_DIR / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    existing_ids = {r["id"] for r in index.get("resources", [])}
    published = []
    pdf_dir = LEARNING_DIR / "files" / "pdf"; docx_dir = LEARNING_DIR / "files" / "docx"; text_dir = LEARNING_DIR / "text"
    for folder in (pdf_dir, docx_dir, text_dir): folder.mkdir(parents=True, exist_ok=True)
    for doc in manifest["documents"]:
        choice = mapping_by_key.get(doc["key"])
        if not choice:
            continue
        tool = _safe_text(choice.get("tool"), 60)
        level = _safe_text(choice.get("level"), 30)
        title = _safe_text(choice.get("title"), 240) or doc["title"]
        if tool not in TOOL_MAP or level not in LEVELS:
            raise ValueError(f"Invalid primary tool or level for {title}.")
        rid_base = "custom-" + _slugify(title)
        rid = rid_base; n = 2
        while rid in existing_ids:
            rid = f"{rid_base}-{n}"; n += 1
        existing_ids.add(rid)
        files = doc["files"]
        pdf_file = ""; docx_file = ""; text = ""
        if files.get("pdf"):
            src = stage / "files" / files["pdf"]
            dest = pdf_dir / f"{rid}.pdf"; shutil.copy2(src, dest); pdf_file = dest.relative_to(LEARNING_DIR).as_posix()
        if files.get("docx"):
            src = stage / "files" / files["docx"]
            raw = src.read_bytes(); text = _extract_docx_text(raw)
            dest = docx_dir / f"{rid}.docx"; shutil.copy2(src, dest); docx_file = dest.relative_to(LEARNING_DIR).as_posix()
        for ext in ("txt", "md", "html", "htm"):
            if not text and files.get(ext):
                text = (stage / "files" / files[ext]).read_text(encoding="utf-8", errors="ignore")
        pages = _chunk_pages(text)
        text_file_path = text_dir / f"{rid}.json"
        text_payload = {"id": rid, "title": title, "pages": pages, "page_count": len(pages), "word_count": len(text.split())}
        text_file_path.write_text(_json_value(text_payload), encoding="utf-8")
        headings = [line.strip() for line in text.splitlines() if re.match(r"^(chapter|module|section|unit|part)\b", line.strip(), re.I)][:40]
        resource = {
            "id": rid, "volume": "Custom", "title": title,
            "summary": " ".join(text.split()[:100]) + ("…" if len(text.split()) > 100 else ""),
            "tools": [tool], "primary_tool": tool, "tool_names": [TOOL_MAP[tool]["name"]],
            "page_count": len(pages), "word_count": len(text.split()), "heading_count": len(headings), "headings": headings,
            "pdf_file": pdf_file, "docx_file": docx_file, "text_file": text_file_path.relative_to(LEARNING_DIR).as_posix(),
            "pdf_bytes": (LEARNING_DIR / pdf_file).stat().st_size if pdf_file else 0,
            "docx_bytes": (LEARNING_DIR / docx_file).stat().st_size if docx_file else 0,
            "related_topics": [], "placement": "tool", "collection": "tool-library", "level": level,
            "classification_method": "Administrator-approved verified import",
            "classification_rationale": _safe_text(choice.get("rationale"), 800) or f"Administrator assigned this document to {TOOL_MAP[tool]['name']} after reviewing the import recommendation.",
            "classification_confidence": "Administrator verified", "resource_type": "Imported course book",
            "library_label": f"Custom · {level}", "version": _safe_text(choice.get("version"), 40) or "1.0",
        }
        index["resources"].append(resource)
        published.append(resource)
        with _connect() as conn:
            conn.execute("INSERT INTO content_versions(resource_id,title,primary_tool,level,version,status,source_file,added_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", (rid, title, tool, level, resource["version"], "active", row["zip_name"], now_iso(), now_iso()))
            conn.commit()
    if not published:
        raise ValueError("Select at least one document to publish.")
    index["resource_count"] = len(index["resources"])
    index["version"] = "2.6.2"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["published_resources"] = [{"id": r["id"], "title": r["title"], "primary_tool": r["primary_tool"], "level": r["level"]} for r in published]
    with _connect() as conn:
        conn.execute("UPDATE content_imports SET status='published',manifest_json=?,published_at=? WHERE id=?", (_json_value(manifest), now_iso(), import_id))
        conn.commit()
    return {"published": len(published), "resources": manifest["published_resources"], "reload_required": True}


def list_content_versions() -> list[dict[str, Any]]:
    with _connect() as conn:
        return [_row(r) for r in conn.execute("SELECT * FROM content_versions ORDER BY updated_at DESC").fetchall()]


def stage_offline_update(file_name: str, content_base64: str) -> dict[str, Any]:
    raw = base64.b64decode(content_base64, validate=True)
    if len(raw) > 500 * 1024 * 1024:
        raise ValueError("Update package exceeds 500 MB.")
    update_id = "upd_" + secrets.token_hex(8)
    folder = UPDATE_DIR / update_id; folder.mkdir(parents=True, exist_ok=True)
    target = folder / "update.zip"; target.write_bytes(raw)
    detected = "unknown"
    try:
        with zipfile.ZipFile(target) as zf:
            _validate_zip_members(zf, max_files=10000, max_total=2 * 1024 * 1024 * 1024, max_member=500 * 1024 * 1024)
            version_candidates = [n for n in zf.namelist() if n.endswith("VERSION.txt") and ".." not in PurePosixPath(n).parts]
            if not version_candidates:
                raise ValueError("Update package does not contain VERSION.txt.")
            detected = zf.read(version_candidates[0]).decode("utf-8", errors="ignore").strip()[:40]
            dangerous = [n for n in zf.namelist() if PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts]
            if dangerous:
                raise ValueError("Update package contains unsafe paths.")
    except zipfile.BadZipFile as exc:
        shutil.rmtree(folder, ignore_errors=True)
        raise ValueError("Update ZIP is invalid.") from exc
    except ValueError:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    digest = hashlib.sha256(raw).hexdigest()
    pending = {"id": update_id, "file_name": _safe_text(file_name, 240), "detected_version": detected, "sha256": digest, "path": str(target), "staged_at": now_iso()}
    (UPDATE_DIR / "pending_update.json").write_text(_json_value(pending), encoding="utf-8")
    with _connect() as conn:
        conn.execute("INSERT INTO update_records(id,file_name,detected_version,sha256,status,staged_path,created_at) VALUES(?,?,?,?,?,?,?)", (update_id, pending["file_name"], detected, digest, "staged", str(target), now_iso()))
        conn.commit()
    return {"staged": True, **pending, "message": "Update verified and staged. Close the bot and run Apply_Pending_Update.bat."}


def list_updates() -> list[dict[str, Any]]:
    with _connect() as conn:
        return [_row(r) for r in conn.execute("SELECT * FROM update_records ORDER BY created_at DESC").fetchall()]


def admin_report_csv() -> bytes:
    overview = admin_overview()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Student", "Email", "Active", "Lessons", "Labs", "Average", "Tests", "Interviews", "Practical Exams", "Last Active"])
    for s in overview["students"]:
        p = s["progress"]
        writer.writerow([s["name"], s["email"], "Yes" if s["active"] else "No", p["lessons"], p["labs"], p["average_score"], p["tests"], p["interviews"], p["practical_exams"], s["last_active"]])
    return out.getvalue().encode("utf-8-sig")


def storage_usage() -> dict[str, Any]:
    def folder_size(path: Path) -> int:
        return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0
    return {
        "application_bytes": folder_size(BASE_DIR), "learning_library_bytes": folder_size(LEARNING_DIR),
        "workspace_bytes": folder_size(WORKSPACE_DIR), "backup_bytes": folder_size(BACKUP_DIR),
        "certificate_bytes": folder_size(CERT_DIR), "database_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
    }
