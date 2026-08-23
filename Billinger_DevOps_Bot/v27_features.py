"""Billinger v2.7 final-readiness and mastery stabilization features.

Standard-library only. Adds a first-run readiness workflow, deterministic baseline
assessment, rigorous mastery gates, safe environment checks, backup-health
verification, and course-freshness metadata. Online provider model discovery is
implemented in v26_features and surfaced through this release.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = Path(os.environ.get("BILLINGER_DB_PATH", str(DATA_DIR / "billinger.db"))).resolve()
VERSION = "2.9.0"

CATALOG = json.loads((CONTENT_DIR / "devops_catalog.json").read_text(encoding="utf-8"))
QUESTION_DATA = json.loads((CONTENT_DIR / "question_bank.json").read_text(encoding="utf-8"))
COMPANY = json.loads((CONTENT_DIR / "company_scenarios.json").read_text(encoding="utf-8"))
TOOLS = CATALOG["tools"]
TOOL_MAP = {t["slug"]: t for t in TOOLS}
LEVELS = ["Beginner", "Intermediate", "Advanced", "Master"]

OFFICIAL_DOCS = {
    "linux": "https://www.kernel.org/doc/html/latest/",
    "networking": "https://www.rfc-editor.org/",
    "git": "https://git-scm.com/docs",
    "shell": "https://www.gnu.org/software/bash/manual/",
    "python-automation": "https://docs.python.org/3/",
    "docker": "https://docs.docker.com/",
    "kubernetes": "https://kubernetes.io/docs/",
    "cicd": "https://docs.github.com/actions",
    "jenkins": "https://www.jenkins.io/doc/",
    "github-actions": "https://docs.github.com/actions",
    "terraform": "https://developer.hashicorp.com/terraform/docs",
    "ansible": "https://docs.ansible.com/",
    "aws": "https://docs.aws.amazon.com/",
    "azure": "https://learn.microsoft.com/azure/",
    "gcp": "https://cloud.google.com/docs",
    "observability": "https://opentelemetry.io/docs/",
    "logging": "https://opensearch.org/docs/latest/",
    "devsecops": "https://slsa.dev/spec/",
    "sre": "https://sre.google/books/",
    "system-design": "https://12factor.net/",
    "databases": "https://www.postgresql.org/docs/",
}

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS readiness_state (
    student_id INTEGER PRIMARY KEY,
    wizard_seen INTEGER NOT NULL DEFAULT 0,
    wizard_completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS baseline_assessments (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    questions_json TEXT NOT NULL,
    answers_json TEXT NOT NULL DEFAULT '[]',
    score REAL NOT NULL DEFAULT 0,
    classification TEXT NOT NULL DEFAULT '',
    domain_scores_json TEXT NOT NULL DEFAULT '{}',
    recommended_start TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS environment_checks (
    id TEXT PRIMARY KEY,
    student_id INTEGER,
    results_json TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS backup_health_checks (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    backup_id TEXT NOT NULL DEFAULT '',
    detail_json TEXT NOT NULL,
    checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS course_freshness (
    tool TEXT PRIMARY KEY,
    course_version TEXT NOT NULL,
    tool_version_covered TEXT NOT NULL DEFAULT '',
    official_doc_url TEXT NOT NULL DEFAULT '',
    last_reviewed TEXT NOT NULL DEFAULT '',
    review_status TEXT NOT NULL DEFAULT 'review_required',
    deprecated_notes TEXT NOT NULL DEFAULT '',
    reviewer TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
"""


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        try:
            return bool(super().__exit__(exc_type, exc, tb))
        finally:
            self.close()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def clean_text(value: Any, max_len: int = 100_000) -> str:
    return str(value or "").replace("\x00", "").strip()[:max_len]


def init_v27_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with db_connect() as conn:
        conn.executescript(SCHEMA)
        for tool in TOOLS:
            conn.execute(
                """INSERT OR IGNORE INTO course_freshness(
                    tool,course_version,tool_version_covered,official_doc_url,last_reviewed,
                    review_status,deprecated_notes,reviewer,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    tool["slug"], "Billinger curriculum 2.7", "See assigned verified course volumes",
                    OFFICIAL_DOCS.get(tool["slug"], ""), "", "review_required", "", "", now_iso(),
                ),
            )
        for row in conn.execute("SELECT id FROM students").fetchall():
            conn.execute(
                "INSERT OR IGNORE INTO readiness_state(student_id,updated_at) VALUES(?,?)",
                (int(row["id"]), now_iso()),
            )


def _student_exists(student_id: int) -> bool:
    with db_connect() as conn:
        return conn.execute("SELECT 1 FROM students WHERE id=?", (student_id,)).fetchone() is not None


def _profile(student_id: int) -> dict[str, Any]:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT s.name,s.email,p.target_role,p.study_minutes,p.interview_date,p.active_track "
            "FROM students s LEFT JOIN student_profiles p ON p.student_id=s.id WHERE s.id=?",
            (student_id,),
        ).fetchone()
    return dict(row) if row else {}


def _latest_baseline(student_id: int) -> dict[str, Any] | None:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT * FROM baseline_assessments WHERE student_id=? ORDER BY started_at DESC,rowid DESC LIMIT 1",
            (student_id,),
        ).fetchone()
    if not row:
        return None
    item = dict(row)
    item["domain_scores"] = json.loads(item.pop("domain_scores_json") or "{}")
    item.pop("questions_json", None)
    item.pop("answers_json", None)
    return item


def _latest_environment(student_id: int) -> dict[str, Any] | None:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT * FROM environment_checks WHERE student_id=? ORDER BY checked_at DESC,rowid DESC LIMIT 1",
            (student_id,),
        ).fetchone()
    if not row:
        return None
    return {"id": row["id"], "checked_at": row["checked_at"], "results": json.loads(row["results_json"])}


def latest_environment(student_id: int) -> dict[str, Any] | None:
    """Return the latest stored read-only environment scan for a student."""
    return _latest_environment(student_id)


def _latest_backup_health() -> dict[str, Any] | None:
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM backup_health_checks ORDER BY checked_at DESC,rowid DESC LIMIT 1").fetchone()
    if not row:
        return None
    return {
        "id": row["id"], "status": row["status"], "backup_id": row["backup_id"],
        "detail": json.loads(row["detail_json"]), "checked_at": row["checked_at"],
    }


def _today_plan_exists(student_id: int) -> bool:
    today = dt.date.today().isoformat()
    with db_connect() as conn:
        return conn.execute(
            "SELECT 1 FROM daily_plans WHERE student_id=? AND plan_date=?", (student_id, today)
        ).fetchone() is not None


def _successful_ai_count() -> int:
    with db_connect() as conn:
        try:
            return int(conn.execute("SELECT COUNT(*) FROM ai_providers WHERE last_status='ready' AND enabled=1 AND key_blob IS NOT NULL").fetchone()[0])
        except sqlite3.OperationalError:
            return 0


def readiness_status(student_id: int, library_count: int = 0, admin_configured: bool = False) -> dict[str, Any]:
    if not _student_exists(student_id):
        raise ValueError("Student not found.")
    profile = _profile(student_id)
    baseline = _latest_baseline(student_id)
    environment = _latest_environment(student_id)
    backup = backup_health(record=False)
    with db_connect() as conn:
        state = conn.execute("SELECT * FROM readiness_state WHERE student_id=?", (student_id,)).fetchone()
        if not state:
            conn.execute("INSERT INTO readiness_state(student_id,updated_at) VALUES(?,?)", (student_id, now_iso()))
            state = conn.execute("SELECT * FROM readiness_state WHERE student_id=?", (student_id,)).fetchone()
    steps = [
        {"id": "admin", "label": "Administrator configured", "required": True, "complete": bool(admin_configured), "detail": "Protects provider keys, imports, backups and institute settings."},
        {"id": "profile", "label": "Learner goal and study time", "required": True, "complete": bool(profile.get("target_role") and int(profile.get("study_minutes") or 0) >= 20), "detail": f"{profile.get('target_role') or 'Not selected'} · {profile.get('study_minutes') or 0} minutes/day"},
        {"id": "baseline", "label": "Baseline assessment", "required": True, "complete": bool(baseline and baseline.get("status") == "completed"), "detail": (f"{baseline.get('classification')} · {baseline.get('score')}%" if baseline else "Not completed")},
        {"id": "library", "label": "Verified learning library", "required": True, "complete": library_count > 0, "detail": f"{library_count} classified resources available"},
        {"id": "environment", "label": "Local lab environment checked", "required": False, "complete": bool(environment), "detail": (environment.get("checked_at", "") if environment else "Run a safe read-only scan")},
        {"id": "ai", "label": "At least one AI provider tested", "required": False, "complete": _successful_ai_count() > 0, "detail": f"{_successful_ai_count()} provider(s) ready; online AI is optional"},
        {"id": "backup", "label": "Verified backup created", "required": True, "complete": backup.get("status") == "healthy", "detail": backup.get("summary", "No verified backup")},
        {"id": "plan", "label": "First daily plan generated", "required": True, "complete": _today_plan_exists(student_id), "detail": "Today’s evidence-based learning sequence"},
    ]
    required = [x for x in steps if x["required"]]
    complete = all(x["complete"] for x in required)
    if complete and not bool(state["wizard_completed"]):
        with db_connect() as conn:
            conn.execute(
                "UPDATE readiness_state SET wizard_seen=1,wizard_completed=1,completed_at=?,updated_at=? WHERE student_id=?",
                (now_iso(), now_iso(), student_id),
            )
    score = round(sum(1 for x in steps if x["complete"]) / len(steps) * 100)
    return {
        "version": VERSION, "student_id": student_id, "ready_to_learn": complete,
        "readiness_percent": score, "steps": steps, "profile": profile, "baseline": baseline,
        "environment": environment, "backup": backup,
        "wizard_seen": bool(state["wizard_seen"]), "wizard_completed": complete or bool(state["wizard_completed"]),
        "notice": "Online AI and real-tool installations are optional. The verified local course remains available without them.",
    }


def mark_wizard_seen(student_id: int) -> dict[str, Any]:
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO readiness_state(student_id,wizard_seen,updated_at) VALUES(?,1,?) "
            "ON CONFLICT(student_id) DO UPDATE SET wizard_seen=1,updated_at=excluded.updated_at",
            (student_id, now_iso()),
        )
    return {"saved": True}


def _baseline_pool() -> list[dict[str, Any]]:
    # Foundational and cross-functional areas. Questions remain deterministic and
    # are selected from the verified local question bank.
    desired = [
        "linux", "networking", "git", "shell", "docker", "kubernetes", "terraform",
        "devsecops", "sre", "system-design",
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in QUESTION_DATA.get("questions", []):
        if q.get("tool") in desired and q.get("type") == "mcq":
            grouped[q["tool"]].append(q)
    out: list[dict[str, Any]] = []
    # Two questions per domain gives a balanced 20-question starting assessment.
    for slug in desired:
        rows = grouped.get(slug, [])
        rows = sorted(rows, key=lambda x: (LEVELS.index(x.get("difficulty", "Beginner")) if x.get("difficulty") in LEVELS else 0, x.get("id", "")))
        if rows:
            first = next((q for q in rows if q.get("difficulty") == "Beginner"), rows[0])
            stretch = next((q for q in rows if q.get("difficulty") in {"Intermediate", "Advanced"}), rows[min(1, len(rows)-1)])
            out.append(first)
            if stretch["id"] != first["id"]:
                out.append(stretch)
    return out[:20]


def start_baseline(student_id: int) -> dict[str, Any]:
    if not _student_exists(student_id):
        raise ValueError("Student not found.")
    pool = _baseline_pool()
    if len(pool) < 10:
        raise ValueError("The verified question bank is unavailable for baseline assessment.")
    session_id = "BASE-" + secrets.token_urlsafe(10)
    public = [
        {
            "id": q["id"], "tool": q["tool"], "difficulty": q.get("difficulty", "Beginner"),
            "prompt": q["prompt"], "choices": q.get("choices", []),
        }
        for q in pool
    ]
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO baseline_assessments(id,student_id,questions_json,started_at) VALUES(?,?,?,?)",
            (session_id, student_id, json.dumps([q["id"] for q in pool]), now_iso()),
        )
    return {"session_id": session_id, "questions": public, "count": len(public), "passive": True}


def submit_baseline(student_id: int, session_id: str, answers: list[dict[str, Any]]) -> dict[str, Any]:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT * FROM baseline_assessments WHERE id=? AND student_id=?", (session_id, student_id)
        ).fetchone()
    if not row or row["status"] != "active":
        raise ValueError("Baseline session is missing or already completed.")
    ids = json.loads(row["questions_json"])
    qmap = {q["id"]: q for q in QUESTION_DATA.get("questions", [])}
    amap = {clean_text(a.get("id"), 100): a.get("answer") for a in answers if isinstance(a, dict)}
    details: list[dict[str, Any]] = []
    domain_total: dict[str, int] = defaultdict(int)
    domain_correct: dict[str, int] = defaultdict(int)
    correct = 0
    for qid in ids:
        q = qmap.get(qid)
        if not q:
            continue
        try:
            selected = int(amap.get(qid, -1))
        except (TypeError, ValueError):
            selected = -1
        is_correct = selected == int(q.get("answer", -2))
        correct += int(is_correct)
        domain_total[q["tool"]] += 1
        domain_correct[q["tool"]] += int(is_correct)
        details.append({
            "id": qid, "tool": q["tool"], "correct": is_correct,
            "selected": selected, "correct_answer": q.get("answer"),
            "explanation": q.get("explanation", ""),
        })
    score = round(correct / max(1, len(ids)) * 100, 1)
    if score < 40:
        classification = "Complete beginner"
    elif score < 60:
        classification = "Foundation learner"
    elif score < 75:
        classification = "Junior-ready learner"
    elif score < 90:
        classification = "Intermediate learner"
    else:
        classification = "Advanced learner"
    domain_scores = {
        slug: round(domain_correct[slug] / max(1, total) * 100, 1)
        for slug, total in domain_total.items()
    }
    recommended = min(domain_scores, key=domain_scores.get) if domain_scores else "linux"
    with db_connect() as conn:
        conn.execute(
            """UPDATE baseline_assessments SET answers_json=?,score=?,classification=?,
               domain_scores_json=?,recommended_start=?,status='completed',completed_at=? WHERE id=?""",
            (json.dumps(answers), score, classification, json.dumps(domain_scores), recommended, now_iso(), session_id),
        )
    return {
        "session_id": session_id, "score": score, "classification": classification,
        "domain_scores": domain_scores, "recommended_start": recommended,
        "recommended_start_name": TOOL_MAP.get(recommended, {}).get("name", recommended),
        "details": details,
        "message": "The baseline sets a starting recommendation; it does not skip required mastery evidence.",
    }


def _tool_assets() -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, set[str]], dict[str, str], dict[str, str]]:
    lessons: dict[str, set[str]] = defaultdict(set)
    labs: dict[str, set[str]] = defaultdict(set)
    tickets: dict[str, set[str]] = defaultdict(set)
    incidents: dict[str, str] = {}
    capstones: dict[str, str] = {}
    for tool in TOOLS:
        slug = tool["slug"]
        for level in tool["levels"]:
            lessons[slug].update(x["id"] for x in level.get("lessons", []))
            labs[slug].update(x["id"] for x in level.get("labs", []))
    for item in COMPANY.get("tickets", []):
        tickets[item.get("tool", "")].add(item["id"])
    for item in COMPANY.get("incidents", []):
        incidents[item.get("tool", "")] = item["id"]
    for item in COMPANY.get("capstones", []):
        capstones[item.get("tool", "")] = item["id"]
    return lessons, labs, tickets, incidents, capstones


def mastery_gates(student_id: int) -> dict[str, Any]:
    lessons, labs, tickets, incidents, capstones = _tool_assets()
    with db_connect() as conn:
        progress = [dict(r) for r in conn.execute("SELECT item_type,item_id,status,score FROM progress WHERE student_id=?", (student_id,)).fetchall()]
        practical = [dict(r) for r in conn.execute("SELECT tool,level,status,score FROM practical_exam_runs WHERE student_id=?", (student_id,)).fetchall()]
        ticket_runs = [dict(r) for r in conn.execute("SELECT ticket_id,status,score FROM company_ticket_runs WHERE student_id=?", (student_id,)).fetchall()]
        incident_runs = [dict(r) for r in conn.execute("SELECT incident_id,status,score FROM incident_runs WHERE student_id=?", (student_id,)).fetchall()]
        capstone_runs = [dict(r) for r in conn.execute("SELECT capstone_id,status,score FROM capstone_runs WHERE student_id=?", (student_id,)).fetchall()]
        portfolio = [dict(r) for r in conn.execute("SELECT tools_json,status,score FROM portfolio_projects WHERE student_id=?", (student_id,)).fetchall()]
    prog_by = {(x["item_type"], x["item_id"]): x for x in progress}
    ticket_best: dict[str, float] = defaultdict(float)
    for r in ticket_runs:
        if r["status"] == "passed": ticket_best[r["ticket_id"]] = max(ticket_best[r["ticket_id"]], float(r["score"]))
    incident_best: dict[str, float] = defaultdict(float)
    for r in incident_runs:
        if r["status"] == "passed": incident_best[r["incident_id"]] = max(incident_best[r["incident_id"]], float(r["score"]))
    capstone_best: dict[str, float] = defaultdict(float)
    for r in capstone_runs:
        if r["status"] == "passed": capstone_best[r["capstone_id"]] = max(capstone_best[r["capstone_id"]], float(r["score"]))
    practical_by: dict[str, dict[str, float]] = defaultdict(dict)
    for r in practical:
        if r["status"] == "completed" and float(r["score"]) >= 80:
            practical_by[r["tool"]][r["level"]] = max(practical_by[r["tool"]].get(r["level"], 0), float(r["score"]))
    portfolio_tools: dict[str, float] = defaultdict(float)
    for r in portfolio:
        if r["status"] not in {"portfolio_ready", "approved"} or float(r["score"]) < 80:
            continue
        try:
            values = json.loads(r["tools_json"])
        except Exception:
            values = []
        for slug in values:
            portfolio_tools[slug] = max(portfolio_tools[slug], float(r["score"]))

    items = []
    for tool in TOOLS:
        slug = tool["slug"]
        lesson_done = sum(1 for lid in lessons[slug] if prog_by.get(("lesson", lid), {}).get("status") == "completed")
        lab_done = sum(1 for lid in labs[slug] if prog_by.get(("lab", lid), {}).get("status") == "passed")
        test = prog_by.get(("test", slug), {})
        interview = prog_by.get(("interview", slug), {})
        requirements = [
            {"id": "lessons", "label": "Lessons completed", "current": lesson_done, "target": len(lessons[slug]), "complete": lesson_done >= len(lessons[slug])},
            {"id": "labs", "label": "Guided labs passed", "current": lab_done, "target": len(labs[slug]), "complete": lab_done >= len(labs[slug])},
            {"id": "test", "label": "Knowledge test", "current": round(float(test.get("score", 0)), 1), "target": 85, "unit": "%", "complete": test.get("status") == "passed" and float(test.get("score", 0)) >= 85},
            {"id": "practical", "label": "Practical levels passed", "current": len(practical_by.get(slug, {})), "target": 4, "complete": len(practical_by.get(slug, {})) >= 4},
            {"id": "tickets", "label": "Company tickets passed", "current": sum(1 for tid in tickets[slug] if ticket_best.get(tid, 0) > 0), "target": len(tickets[slug]), "complete": all(ticket_best.get(tid, 0) > 0 for tid in tickets[slug])},
            {"id": "incident", "label": "Production incident", "current": round(incident_best.get(incidents.get(slug, ""), 0), 1), "target": 78, "unit": "%", "complete": incident_best.get(incidents.get(slug, ""), 0) >= 78},
            {"id": "capstone", "label": "Enterprise capstone", "current": round(capstone_best.get(capstones.get(slug, ""), 0), 1), "target": 82, "unit": "%", "complete": capstone_best.get(capstones.get(slug, ""), 0) >= 82},
            {"id": "interview", "label": "Mock interview", "current": round(float(interview.get("score", 0)), 1), "target": 80, "unit": "%", "complete": interview.get("status") == "passed" and float(interview.get("score", 0)) >= 80},
            {"id": "portfolio", "label": "Verified portfolio evidence", "current": round(portfolio_tools.get(slug, 0), 1), "target": 80, "unit": "%", "complete": portfolio_tools.get(slug, 0) >= 80},
        ]
        pct = round(sum(1 for x in requirements if x["complete"]) / len(requirements) * 100)
        items.append({
            "tool": slug, "name": tool["name"], "icon": tool["icon"], "percent": pct,
            "mastered": all(x["complete"] for x in requirements), "requirements": requirements,
        })
    return {
        "student_id": student_id, "tools": items,
        "mastered_count": sum(1 for x in items if x["mastered"]), "total_tools": len(items),
        "policy": "A tool is marked mastered only after learning, lab, assessment, company, incident, capstone, interview and portfolio evidence all pass their gates.",
    }


def _command_version(command: list[str], timeout: int = 4) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        text = (result.stdout or result.stderr or "").strip().splitlines()
        return clean_text(text[0] if text else "Detected", 200)
    except Exception as exc:
        return f"Detected; version check unavailable ({type(exc).__name__})"


def check_environment(student_id: int | None = None) -> dict[str, Any]:
    # Every command is fixed by the application; user input is never executed.
    tools = [
        ("python", [["python", "--version"], ["py", "-V"], ["python3", "--version"]], "Core runtime", True),
        ("git", [["git", "--version"]], "Real Git project workflow", False),
        ("wsl", [["wsl", "--status"]], "Linux practice environment", False),
        ("docker", [["docker", "version", "--format", "{{.Client.Version}}"]], "Container labs", False),
        ("kubectl", [["kubectl", "version", "--client=true"]], "Kubernetes labs", False),
        ("terraform", [["terraform", "version"]], "Infrastructure-as-code labs", False),
        ("ansible", [["ansible", "--version"]], "Configuration-management labs", False),
        ("aws", [["aws", "--version"]], "AWS CLI exercises", False),
        ("az", [["az", "version"]], "Azure CLI exercises", False),
        ("gcloud", [["gcloud", "version"]], "Google Cloud CLI exercises", False),
    ]
    rows = []
    for name, candidates, purpose, required in tools:
        command = next((candidate for candidate in candidates if shutil.which(candidate[0])), candidates[0])
        path = shutil.which(command[0])
        installed = bool(path)
        version = _command_version(command) if installed else "Not installed"
        rows.append({
            "name": name, "installed": installed, "path": path or "", "version": version,
            "purpose": purpose, "required_for_core": required,
        })
    result = {
        "checked_at": now_iso(), "core_ready": any(x["name"] == "python" and x["installed"] for x in rows),
        "tools": rows,
        "modes": [
            {"id": "guided", "label": "Guided learning", "description": "Read and explain verified course content."},
            {"id": "simulation", "label": "Safe simulation", "description": "Evaluate plans and evidence without changing the host."},
            {"id": "local", "label": "Real local execution", "description": "Use installed tools in a controlled workspace."},
            {"id": "cloud", "label": "External cloud lab", "description": "Requires a separately controlled cloud account and cost safeguards."},
            {"id": "company", "label": "Simulated company scenario", "description": "Ticket, incident, review and communication practice."},
        ],
    }
    check_id = "ENV-" + secrets.token_urlsafe(9)
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO environment_checks(id,student_id,results_json,checked_at) VALUES(?,?,?,?)",
            (check_id, student_id, json.dumps(result), result["checked_at"]),
        )
    return {"id": check_id, **result}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_health(record: bool = True) -> dict[str, Any]:
    """Verify the latest application backup without accepting a user-supplied path.

    ``record=False`` is used by passive readiness views so merely opening a page
    cannot grow the database. Explicit administrator checks remain auditable.
    """
    with db_connect() as conn:
        try:
            row = conn.execute("SELECT * FROM backup_records ORDER BY created_at DESC,rowid DESC LIMIT 1").fetchone()
        except sqlite3.OperationalError:
            row = None
    if not row:
        result = {"status": "missing", "summary": "No verified backup has been created yet.", "latest": None}
    else:
        path = (BACKUP_DIR / row["file_name"]).resolve()
        safe_root = BACKUP_DIR.resolve()
        path_allowed = path.parent == safe_root
        detail: dict[str, Any] = {
            "file": row["file_name"], "recorded_sha256": row["sha256"],
            "exists": path.is_file() and path_allowed, "path_allowed": path_allowed,
        }
        status = "unhealthy"
        if detail["exists"]:
            digest = _sha256_file(path)
            detail["actual_sha256"] = digest
            detail["checksum_ok"] = secrets.compare_digest(digest, str(row["sha256"]))
            try:
                with zipfile.ZipFile(path) as zf:
                    bad = zf.testzip()
                    detail["zip_integrity"] = bad is None
                    detail["bad_member"] = bad or ""
            except Exception as exc:
                detail["zip_integrity"] = False
                detail["error"] = clean_text(exc, 300)
            if detail.get("checksum_ok") and detail.get("zip_integrity"):
                status = "healthy"
        result = {
            "status": status,
            "summary": (f"Latest backup {row['file_name']} passed checksum and ZIP integrity." if status == "healthy" else f"Latest backup {row['file_name']} failed integrity verification."),
            "latest": {"id": row["id"], "created_at": row["created_at"], "size_bytes": row["size_bytes"], **detail},
        }
    if record:
        check_id = "BHC-" + secrets.token_urlsafe(8)
        with db_connect() as conn:
            conn.execute(
                "INSERT INTO backup_health_checks(id,status,backup_id,detail_json,checked_at) VALUES(?,?,?,?,?)",
                (check_id, result["status"], (result.get("latest") or {}).get("id", ""), json.dumps(result), now_iso()),
            )
        return {"check_id": check_id, **result}
    return {"check_id": "", **result}


def freshness_dashboard() -> dict[str, Any]:
    with db_connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM course_freshness ORDER BY tool").fetchall()]
        try:
            proposal_count = int(conn.execute("SELECT COUNT(*) FROM ai_curriculum_proposals WHERE status='review_required'").fetchone()[0])
        except sqlite3.OperationalError:
            proposal_count = 0
    items = []
    for row in rows:
        tool = TOOL_MAP.get(row["tool"], {})
        reviewed = row["last_reviewed"]
        age_days = None
        if reviewed:
            try:
                age_days = (dt.date.today() - dt.date.fromisoformat(reviewed[:10])).days
            except Exception:
                pass
        status = row["review_status"]
        if age_days is not None and age_days > 180 and status == "current":
            status = "review_due"
        items.append({**row, "name": tool.get("name", row["tool"]), "icon": tool.get("icon", "•"), "age_days": age_days, "effective_status": status})
    return {
        "items": items, "pending_ai_proposals": proposal_count,
        "summary": {
            "current": sum(1 for x in items if x["effective_status"] == "current"),
            "review_due": sum(1 for x in items if x["effective_status"] in {"review_due", "review_required"}),
            "deprecated": sum(1 for x in items if x["effective_status"] == "deprecated"),
        },
        "notice": "Freshness status is an administrator record. AI recommendations do not mark content current without official-source review.",
    }


def save_freshness(data: dict[str, Any]) -> dict[str, Any]:
    tool = clean_text(data.get("tool"), 80)
    if tool not in TOOL_MAP:
        raise ValueError("Unknown DevOps tool.")
    status = clean_text(data.get("review_status"), 40) or "review_required"
    if status not in {"current", "review_due", "review_required", "deprecated"}:
        raise ValueError("Invalid review status.")
    official = clean_text(data.get("official_doc_url"), 1000) or OFFICIAL_DOCS.get(tool, "")
    if official and not official.startswith("https://"):
        raise ValueError("Official documentation URL must use HTTPS.")
    last_reviewed = clean_text(data.get("last_reviewed"), 20)
    if last_reviewed:
        dt.date.fromisoformat(last_reviewed[:10])
    with db_connect() as conn:
        conn.execute(
            """UPDATE course_freshness SET course_version=?,tool_version_covered=?,official_doc_url=?,
               last_reviewed=?,review_status=?,deprecated_notes=?,reviewer=?,updated_at=? WHERE tool=?""",
            (
                clean_text(data.get("course_version"), 120) or "Billinger curriculum 2.7",
                clean_text(data.get("tool_version_covered"), 200), official, last_reviewed, status,
                clean_text(data.get("deprecated_notes"), 4000), clean_text(data.get("reviewer"), 160), now_iso(), tool,
            ),
        )
    return {"saved": True, "tool": tool}


def graduation_summary(student_id: int) -> dict[str, Any]:
    gates = mastery_gates(student_id)
    with db_connect() as conn:
        state = conn.execute("SELECT wizard_completed FROM readiness_state WHERE student_id=?", (student_id,)).fetchone()
    return {
        "ready_to_start": bool(state and state["wizard_completed"]),
        "mastered_tools": gates["mastered_count"], "total_tools": gates["total_tools"],
        "course_mastered": gates["mastered_count"] == gates["total_tools"],
        "next_actions": [
            {"tool": x["tool"], "name": x["name"], "remaining": [r["label"] for r in x["requirements"] if not r["complete"]][:3]}
            for x in gates["tools"] if not x["mastered"]
        ][:5],
    }


def backup_tables() -> list[str]:
    return ["readiness_state", "baseline_assessments", "environment_checks", "backup_health_checks", "course_freshness"]
