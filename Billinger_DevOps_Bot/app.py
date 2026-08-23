#!/usr/bin/env python3
"""Billinger DevOps Learning Bot - lightweight local Windows web application.

No third-party Python packages are required. The server binds to 127.0.0.1 only.
"""
from __future__ import annotations

import argparse
import base64
import collections
import datetime as dt
import hashlib
import html
import io
import json
import mimetypes
import os
import random
import re
import secrets
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile

import v2_features as v2
import v23_features as v23
import v24_features as v24
import v26_features as v26
import v27_features as v27
import xml.etree.ElementTree as ET
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

APP_NAME = "Billinger DevOps Learning Bot — 4K Precision, Dark Accessibility, Adaptive AI, Career & Training Command Centre"
VERSION = "2.9.0"
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CONTENT_DIR = BASE_DIR / "content"
DATA_DIR = BASE_DIR / "data"
RESUME_DIR = BASE_DIR / "resumes"
LEARNING_RESOURCE_DIR = BASE_DIR / "learning_resources"
DB_PATH = Path(os.environ.get("BILLINGER_DB_PATH", str(DATA_DIR / "billinger.db"))).resolve()
MAX_BODY_BYTES = 110 * 1024 * 1024
MAX_STUDENTS = 10
DEFAULT_PORT = 8765
LEVELS = ["Beginner", "Intermediate", "Advanced", "Master"]
PASS_MARKS = {"Beginner": 70, "Intermediate": 75, "Advanced": 80, "Master": 85}

DATA_DIR.mkdir(parents=True, exist_ok=True)
RESUME_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


CATALOG = load_json(CONTENT_DIR / "devops_catalog.json")
QUESTION_DATA = load_json(CONTENT_DIR / "question_bank.json")
INTERVIEW_DATA = load_json(CONTENT_DIR / "interview_bank.json")
QUESTION_MAP = {q["id"]: q for q in QUESTION_DATA["questions"]}
INTERVIEW_MAP = {q["id"]: q for q in INTERVIEW_DATA["questions"]}
TOOL_MAP = {t["slug"]: t for t in CATALOG["tools"]}
RESOURCE_INDEX = load_json(LEARNING_RESOURCE_DIR / "index.json") if (LEARNING_RESOURCE_DIR / "index.json").is_file() else {"resources": []}
RESOURCE_MAP = {r["id"]: r for r in RESOURCE_INDEX.get("resources", [])}

def reload_resource_index() -> None:
    """Reload the learning-resource index after an administrator publishes new material."""
    global RESOURCE_INDEX, RESOURCE_MAP
    RESOURCE_INDEX = load_json(LEARNING_RESOURCE_DIR / "index.json") if (LEARNING_RESOURCE_DIR / "index.json").is_file() else {"resources": []}
    RESOURCE_MAP = {r["id"]: r for r in RESOURCE_INDEX.get("resources", [])}

LESSON_MAP: dict[str, dict[str, Any]] = {}
LAB_MAP: dict[str, dict[str, Any]] = {}
for _tool in CATALOG["tools"]:
    for _level in _tool["levels"]:
        for _lesson in _level["lessons"]:
            LESSON_MAP[_lesson["id"]] = {**_lesson, "tool": _tool["slug"], "level": _level["name"]}
        for _lab in _level["labs"]:
            LAB_MAP[_lab["id"]] = {**_lab, "tool": _tool["slug"], "level": _level["name"]}


def build_coverage_catalog() -> dict[str, Any]:
    """Return an exact, searchable manifest of content bundled in this release."""
    company = v2.COMPANY
    tickets_by: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    incidents_by: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    capstones_by: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    tests_by: collections.Counter[str] = collections.Counter()
    interviews_by: collections.Counter[str] = collections.Counter()
    resources_by: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for resource in RESOURCE_INDEX.get("resources", []):
        resource_tool = resource.get("primary_tool", "")
        if resource.get("placement") == "tool" and resource_tool in TOOL_MAP:
            resources_by[resource_tool].append(resource)
    for item in company.get("tickets", []):
        tickets_by[item.get("tool", "")].append(item)
    for item in company.get("incidents", []):
        incidents_by[item.get("tool", "")].append(item)
    for item in company.get("capstones", []):
        capstones_by[item.get("tool", "")].append(item)
    for item in QUESTION_DATA.get("questions", []):
        tests_by[item.get("tool", "")] += 1
    for item in INTERVIEW_DATA.get("questions", []):
        interviews_by[item.get("tool", "")] += 1

    tools: list[dict[str, Any]] = []
    all_examples: list[str] = []
    for tool in CATALOG["tools"]:
        command_examples: list[str] = []
        levels: list[dict[str, Any]] = []
        for level in tool["levels"]:
            level_commands: list[str] = []
            for lesson in level["lessons"]:
                level_commands.extend(re.findall(r"`([^`]+)`", lesson.get("example", "")))
            command_examples.extend(level_commands)
            levels.append({
                "name": level["name"],
                "company_workflow": level["company_workflow"],
                "mastery_gate": level["mastery_gate"],
                "lesson_titles": [lesson["title"] for lesson in level["lessons"]],
                "commands": sorted(set(level_commands), key=str.lower),
                "labs": [{"id": lab["id"], "title": lab["title"], "scenario": lab["scenario"]} for lab in level["labs"]],
            })
        all_examples.extend(command_examples)
        slug = tool["slug"]
        tools.append({
            "slug": slug, "name": tool["name"], "icon": tool["icon"], "category": tool["category"],
            "description": tool["description"], "why_company": tool["why_company"],
            "lesson_count": sum(len(level["lessons"]) for level in tool["levels"]),
            "lab_count": sum(len(level["labs"]) for level in tool["levels"]),
            "command_examples": sorted(set(command_examples), key=str.lower),
            "command_example_count": len(command_examples),
            "unique_command_count": len(set(command_examples)),
            "test_question_count": tests_by[slug],
            "interview_question_count": interviews_by[slug],
            "levels": levels,
            "tickets": [{"id": x["id"], "level": x["level"], "title": x["title"], "scenario": x["scenario"], "business_impact": x["business_impact"]} for x in tickets_by[slug]],
            "incidents": [{"id": x["id"], "severity": x["severity"], "title": x["title"], "symptoms": x["symptoms"], "customer_impact": x["customer_impact"]} for x in incidents_by[slug]],
            "capstones": [{"id": x["id"], "title": x["title"], "brief": x["brief"]} for x in capstones_by[slug]],
            "learning_resources": [{"id": x["id"], "volume": x["volume"], "library_label": x.get("library_label", f"Volume {x.get('volume', '')}"), "title": x["title"], "page_count": x["page_count"], "primary_tool": x.get("primary_tool", "")} for x in resources_by[slug]],
        })

    return {
        "version": VERSION,
        "scope_notice": "This is a broad, structured DevOps curriculum, not every command or every company-specific situation in existence. Commands and practices vary by operating system, product version, cloud, organization, policy, and job role.",
        "summary": {
            "domains": len(tools),
            "levels": sum(len(t["levels"]) for t in tools),
            "lessons": len(LESSON_MAP),
            "practice_labs": len(LAB_MAP),
            "command_examples": len(all_examples),
            "unique_command_examples": len(set(all_examples)),
            "test_questions": len(QUESTION_DATA.get("questions", [])),
            "interview_questions": len(INTERVIEW_DATA.get("questions", [])),
            "company_tickets": len(company.get("tickets", [])),
            "incidents": len(company.get("incidents", [])),
            "capstones": len(company.get("capstones", [])),
            "learning_resources": len(RESOURCE_INDEX.get("resources", [])),
            "tool_course_books": sum(1 for x in RESOURCE_INDEX.get("resources", []) if x.get("placement") == "tool"),
            "program_guides": sum(1 for x in RESOURCE_INDEX.get("resources", []) if x.get("placement") == "program"),
        },
        "safe_lab": {
            "executables": sorted(v2.ALLOWED_SIMPLE),
            "restricted_subcommands": {k: sorted(values) for k, values in sorted(v2.ALLOWED_SUBCOMMANDS.items())},
            "notice": "Learning examples are wider than executable Safe Lab commands. The Safe Lab intentionally executes only a restricted allowlist; destructive, privileged, remote, and host-administration operations are blocked.",
        },
        "tools": tools,
    }


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    pin_hash TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    last_active TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    status TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    UNIQUE(student_id, item_type, item_id),
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS practice_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    lab_id TEXT NOT NULL,
    response TEXT NOT NULL,
    score REAL NOT NULL,
    feedback TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS test_sessions (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    tool TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    question_ids TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    passed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS interview_sessions (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    tool TEXT NOT NULL,
    state_json TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    passed INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS resumes (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    text_content TEXT NOT NULL,
    html_content TEXT NOT NULL,
    match_score REAL NOT NULL,
    missing_keywords TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS online_questions (
    id TEXT PRIMARY KEY,
    tool TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    prompt TEXT NOT NULL,
    keywords TEXT NOT NULL,
    ideal_answer TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    attribution TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


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


def init_db() -> None:
    with db_connect() as conn:
        conn.executescript(SCHEMA)
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            ts = now_iso()
            conn.execute(
                "INSERT INTO students(name,email,pin_hash,created_at,last_active) VALUES(?,?,?,?,?)",
                ("Student 1", "", "", ts, ts),
            )
    v2.DB_PATH = DB_PATH
    v23.DB_PATH = DB_PATH
    v24.DB_PATH = DB_PATH
    v26.DB_PATH = DB_PATH
    v27.DB_PATH = DB_PATH
    v2.init_v2_db()
    v23.init_v23_db()
    v24.init_v24_db()
    v26.init_v26_db()
    v27.init_v27_db()


def hash_pin(pin: str) -> str:
    if not pin:
        return ""
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_pin(pin: str, stored: str) -> bool:
    if not stored:
        return True
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 120_000).hex()
    return secrets.compare_digest(candidate, digest)


def audit(action: str, detail: str, student_id: int | None = None) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(student_id,action,detail,created_at) VALUES(?,?,?,?)",
            (student_id, action, detail[:2000], now_iso()),
        )


def json_safe_row(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def clean_text(value: Any, max_len: int = 100_000) -> str:
    text = str(value or "").replace("\x00", "").strip()
    return text[:max_len]


def normalize_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9+.#_-]{2,}", text.lower())


STOPWORDS = {
    "the", "and", "for", "that", "with", "from", "this", "have", "will", "your", "you", "are", "was", "were",
    "into", "using", "use", "used", "then", "than", "when", "what", "which", "where", "while", "would", "could",
    "should", "about", "after", "before", "also", "more", "most", "some", "such", "only", "over", "under", "between",
    "through", "each", "other", "their", "there", "these", "those", "been", "being", "because", "very", "just", "does",
    "into", "our", "its", "not", "but", "can", "all", "any", "per", "via", "how", "why", "who", "they", "them",
}


def extract_keywords(text: str, limit: int = 30) -> list[str]:
    counts = collections.Counter(t for t in normalize_tokens(text) if t not in STOPWORDS and len(t) >= 4)
    return [token for token, _ in counts.most_common(limit)]


def public_resource(resource: dict[str, Any]) -> dict[str, Any]:
    links: dict[str, str] = {}
    if resource.get("pdf_file"):
        links["pdf"] = f"/api/resource/file?id={urllib.parse.quote(resource['id'])}&format=pdf"
    if resource.get("docx_file"):
        links["docx"] = f"/api/resource/file?id={urllib.parse.quote(resource['id'])}&format=docx"
    return {
        "id": resource["id"], "volume": resource.get("volume", ""), "title": resource["title"],
        "library_label": resource.get("library_label", f"Volume {resource.get('volume', '')}"),
        "resource_type": resource.get("resource_type", "Course book"),
        "placement": resource.get("placement", "tool"), "collection": resource.get("collection", "tool-library"),
        "summary": resource.get("summary", ""), "tools": resource.get("tools", []),
        "tool_names": resource.get("tool_names", []), "primary_tool": resource.get("primary_tool", ""),
        "primary_tool_name": TOOL_MAP.get(resource.get("primary_tool", ""), {}).get("name", "Program Library"),
        "related_topics": resource.get("related_topics", []),
        "classification_rationale": resource.get("classification_rationale", ""),
        "classification_confidence": resource.get("classification_confidence", ""),
        "page_count": resource.get("page_count", 0), "word_count": resource.get("word_count", 0),
        "heading_count": resource.get("heading_count", 0), "headings": resource.get("headings", []),
        "pdf_bytes": resource.get("pdf_bytes", 0), "docx_bytes": resource.get("docx_bytes", 0),
        "links": links,
    }


def load_resource_text(resource_id: str) -> dict[str, Any]:
    resource = RESOURCE_MAP.get(resource_id)
    if not resource:
        raise ValueError("Learning resource not found.")
    path = (LEARNING_RESOURCE_DIR / resource["text_file"]).resolve()
    if LEARNING_RESOURCE_DIR.resolve() not in path.parents or not path.is_file():
        raise ValueError("Learning resource text is unavailable.")
    return load_json(path)


def list_learning_resources(tool: str = "", student_id: int = 0, collection: str = "") -> dict[str, Any]:
    if tool and tool not in TOOL_MAP:
        raise ValueError("Invalid DevOps domain.")
    allowed_collections = {"", "tool", "program", "all"}
    if collection not in allowed_collections:
        raise ValueError("Invalid learning-library collection.")
    resources = []
    for resource in RESOURCE_INDEX.get("resources", []):
        if tool and not (resource.get("placement") == "tool" and resource.get("primary_tool") == tool):
            continue
        if collection == "tool" and resource.get("placement") != "tool":
            continue
        if collection == "program" and resource.get("placement") != "program":
            continue
        resources.append(resource)
    completion: dict[str, str] = {}
    if student_id and student_exists(student_id):
        with db_connect() as conn:
            rows = conn.execute("SELECT item_id,status FROM progress WHERE student_id=? AND item_type='resource'", (student_id,)).fetchall()
        completion = {row["item_id"]: row["status"] for row in rows}
    def resource_sort_key(resource: dict[str, Any]) -> tuple[int, str]:
        if isinstance(resource.get("sort_order"), (int, float)):
            return int(resource["sort_order"]), str(resource.get("volume", ""))
        volume = str(resource.get("volume", ""))
        match = re.match(r"(\d+)([A-Za-z]?)", volume)
        if match:
            number = int(match.group(1)); part = ord(match.group(2).upper()) - 64 if match.group(2) else 0
            return number * 100 + part, volume
        return 999999, volume.lower()
    items = []
    for resource in sorted(resources, key=resource_sort_key):
        item = public_resource(resource)
        item["status"] = completion.get(resource["id"], "not_started")
        items.append(item)
    return {"resources": items, "count": len(items), "library_count": len(RESOURCE_MAP), "tool": tool, "collection": collection,
            "policy": RESOURCE_INDEX.get("classification_policy", "Strict primary placement") }


def read_learning_resource(resource_id: str) -> dict[str, Any]:
    resource = RESOURCE_MAP.get(resource_id)
    if not resource:
        raise ValueError("Learning resource not found.")
    payload = load_resource_text(resource_id)
    pages: dict[int, list[str]] = collections.defaultdict(list)
    for chunk in payload.get("chunks", []):
        pages[int(chunk.get("page", 0))].append(clean_text(chunk.get("text"), 5000))
    result = public_resource(resource)
    result["pages"] = [{"page": page, "text": "\n\n".join(parts)} for page, parts in sorted(pages.items())]
    result["headings"] = payload.get("headings", resource.get("headings", []))
    return result


RESOURCE_STOPWORDS = STOPWORDS | {"what", "when", "where", "which", "would", "could", "should", "about", "from", "into", "this", "that", "with", "your", "have", "does", "explain", "describe", "book", "document", "course"}


def answer_from_learning_resource(resource_id: str, question: str) -> dict[str, Any]:
    question = clean_text(question, 2000)
    if len(question) < 3:
        raise ValueError("Enter a question about this learning resource.")
    resource = RESOURCE_MAP.get(resource_id)
    if not resource:
        raise ValueError("Learning resource not found.")
    payload = load_resource_text(resource_id)
    q_tokens = [t for t in normalize_tokens(question) if t not in RESOURCE_STOPWORDS]
    q_set = set(q_tokens)
    scored = []
    for index, chunk in enumerate(payload.get("chunks", [])):
        text = clean_text(chunk.get("text"), 6000)
        lower = text.lower()
        tokens = collections.Counter(t for t in normalize_tokens(text) if t not in RESOURCE_STOPWORDS)
        overlap = sum(min(tokens[t], 4) for t in q_set)
        phrase = 4 if question.lower() in lower else 0
        title_bonus = sum(2 for t in q_set if t in resource.get("title", "").lower())
        score = overlap * 3 + phrase + title_bonus
        if score:
            scored.append((score, index, int(chunk.get("page", 0)), text))
    scored.sort(key=lambda x: (-x[0], x[1]))
    selected = scored[:5]
    if not selected:
        return {"mode": "not_found", "answer": "I could not find a relevant passage in this book. Try using a command, chapter topic, service name, or error term from the document.", "sources": [], "resource": public_resource(resource)}

    sources = [{"page": page, "excerpt": text[:650].strip()} for _, _, page, text in selected]
    settings = v2.get_settings()
    if settings.get("ai_enabled"):
        context = "\n\n".join(f"[Page {src['page']}] {src['excerpt']}" for src in sources)
        prompt = (
            f"Use only the following excerpts from {resource['title']} to answer the student's question. "
            "Cite pages in square brackets, do not invent missing facts, and say when the excerpts are insufficient.\n\n"
            f"QUESTION: {question}\n\nEXCERPTS:\n{context}"
        )
        try:
            ai = v2.local_ai_chat([{"role": "user", "content": prompt}], purpose="document-study")
            return {"mode": "local_ai", "answer": ai["content"], "sources": sources, "resource": public_resource(resource)}
        except ValueError:
            pass

    sentence_candidates = []
    for score, _, page, text in selected:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            sentence = sentence.strip(" •-\t")
            if len(sentence) < 35 or len(sentence) > 520:
                continue
            hits = sum(1 for token in q_set if token in sentence.lower())
            if hits:
                sentence_candidates.append((hits, score, page, sentence))
    sentence_candidates.sort(key=lambda x: (-x[0], -x[1], x[2]))
    chosen = []
    seen = set()
    for _, _, page, sentence in sentence_candidates:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        chosen.append(f"{sentence} [Page {page}]")
        if len(chosen) >= 4:
            break
    if not chosen:
        chosen = [f"{src['excerpt']} [Page {src['page']}]" for src in sources[:2]]
    answer = "Source-grounded answer from the book:\n\n" + "\n\n".join(chosen)
    return {"mode": "extractive", "answer": answer, "sources": sources, "resource": public_resource(resource)}


def score_open_answer(answer: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    answer_lower = answer.lower()
    normalized = set(normalize_tokens(answer))
    keys = [k.lower() for k in keywords if k]
    matched = []
    for key in keys:
        if " " in key:
            if key in answer_lower:
                matched.append(key)
        elif key in normalized or key in answer_lower:
            matched.append(key)
    missing = [k for k in keys if k not in matched]
    coverage = len(matched) / max(1, len(keys))
    word_count = len(normalize_tokens(answer))
    structure_bonus = min(20, word_count / 3)
    safety_bonus = 7.5 if any(x in answer_lower for x in ("validate", "verify", "test", "evidence")) else 0
    recovery_bonus = 7.5 if any(x in answer_lower for x in ("rollback", "recover", "restore", "revert")) else 0
    score = min(100.0, coverage * 65 + structure_bonus + safety_bonus + recovery_bonus)
    return round(score, 1), matched, missing


def progress_upsert(student_id: int, item_type: str, item_id: str, status: str, score: float = 0, notes: str = "") -> None:
    with db_connect() as conn:
        conn.execute(
            """
            INSERT INTO progress(student_id,item_type,item_id,status,score,attempts,notes,updated_at)
            VALUES(?,?,?,?,?,1,?,?)
            ON CONFLICT(student_id,item_type,item_id) DO UPDATE SET
                status=excluded.status,
                score=MAX(progress.score, excluded.score),
                attempts=progress.attempts+1,
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (student_id, item_type, item_id, status, score, notes[:5000], now_iso()),
        )


def student_exists(student_id: int) -> bool:
    with db_connect() as conn:
        return conn.execute("SELECT 1 FROM students WHERE id=?", (student_id,)).fetchone() is not None


def student_stats(student_id: int) -> dict[str, Any]:
    total_lessons = len(LESSON_MAP)
    total_labs = len(LAB_MAP)
    with db_connect() as conn:
        rows = conn.execute("SELECT item_type,status,score FROM progress WHERE student_id=?", (student_id,)).fetchall()
        completed_lessons = sum(1 for r in rows if r["item_type"] == "lesson" and r["status"] == "completed")
        passed_labs = sum(1 for r in rows if r["item_type"] == "lab" and r["status"] == "passed")
        passed_tests = sum(1 for r in rows if r["item_type"] == "test" and r["status"] == "passed")
        passed_interviews = sum(1 for r in rows if r["item_type"] == "interview" and r["status"] == "passed")
        avg_row = conn.execute("SELECT AVG(score) FROM progress WHERE student_id=? AND score>0", (student_id,)).fetchone()[0]
        resumes = conn.execute("SELECT COUNT(*) FROM resumes WHERE student_id=?", (student_id,)).fetchone()[0]
    return {
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "lesson_percent": round(completed_lessons / max(1, total_lessons) * 100, 1),
        "total_labs": total_labs,
        "passed_labs": passed_labs,
        "passed_tests": passed_tests,
        "passed_interviews": passed_interviews,
        "average_score": round(float(avg_row or 0), 1),
        "resumes": resumes,
    }


def public_question(q: dict[str, Any]) -> dict[str, Any]:
    out = {"id": q["id"], "type": q.get("type", "open"), "prompt": q["prompt"], "difficulty": q.get("difficulty", "Intermediate")}
    if q.get("choices"):
        out["choices"] = q["choices"]
    if q.get("source_url"):
        out["source_url"] = q["source_url"]
        out["attribution"] = q.get("attribution", "")
    return out


def online_question_map() -> dict[str, dict[str, Any]]:
    with db_connect() as conn:
        rows = conn.execute("SELECT * FROM online_questions").fetchall()
    result = {}
    for row in rows:
        q = json_safe_row(row)
        q["type"] = "open"
        q["keywords"] = json.loads(q["keywords"])
        result[q["id"]] = q
    return result


def get_any_question(question_id: str) -> dict[str, Any] | None:
    if question_id in QUESTION_MAP:
        return QUESTION_MAP[question_id]
    return online_question_map().get(question_id)


def build_test(student_id: int, tool: str, difficulty: str, count: int, include_online: bool) -> dict[str, Any]:
    pool = [q for q in QUESTION_DATA["questions"] if q["tool"] == tool and q["difficulty"] == difficulty]
    target_count = max(3, min(count, 25))
    if tool == "full-devops":
        pool = [q for q in QUESTION_DATA["questions"] if q["tool"] == "full-devops" or q["difficulty"] == difficulty]
    elif len(pool) < target_count:
        # Preserve the requested level first, then fill the session with questions
        # from the same tool so a normal 5-15 question test is always possible.
        requested_ids = {q["id"] for q in pool}
        pool.extend(q for q in QUESTION_DATA["questions"] if q["tool"] == tool and q["id"] not in requested_ids)
    if include_online:
        pool.extend(q for q in online_question_map().values() if q["tool"] in (tool, "full-devops"))
    if not pool:
        raise ValueError("No questions are available for this selection.")
    preferred = [q for q in pool if q.get("difficulty") == difficulty]
    others = [q for q in pool if q.get("difficulty") != difficulty]
    random.shuffle(preferred)
    random.shuffle(others)
    selected = (preferred + others)[:target_count]
    session_id = "test_" + secrets.token_urlsafe(12)
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO test_sessions(id,student_id,tool,difficulty,question_ids,created_at) VALUES(?,?,?,?,?,?)",
            (session_id, student_id, tool, difficulty, json.dumps([q["id"] for q in selected]), now_iso()),
        )
    audit("test_started", f"tool={tool};difficulty={difficulty};count={len(selected)}", student_id)
    return {"session_id": session_id, "pass_mark": PASS_MARKS.get(difficulty, 75), "questions": [public_question(q) for q in selected]}


def grade_test(session_id: str, student_id: int, answers: list[dict[str, Any]]) -> dict[str, Any]:
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM test_sessions WHERE id=? AND student_id=?", (session_id, student_id)).fetchone()
    if not row:
        raise ValueError("Test session was not found.")
    if row["completed_at"]:
        return json.loads(row["result_json"])
    answer_map = {str(a.get("id")): a.get("answer") for a in answers}
    details = []
    scores = []
    for qid in json.loads(row["question_ids"]):
        q = get_any_question(qid)
        if not q:
            continue
        raw = answer_map.get(qid, "")
        if q.get("type") == "mcq":
            try:
                selected_index = int(raw)
            except (TypeError, ValueError):
                selected_index = -1
            score = 100.0 if selected_index == int(q["answer"]) else 0.0
            detail = {
                "id": qid,
                "score": score,
                "correct": score == 100,
                "explanation": q.get("explanation", ""),
                "correct_answer": q.get("choices", [""])[int(q["answer"])],
            }
        else:
            score, matched, missing = score_open_answer(clean_text(raw, 20_000), q.get("keywords", []))
            detail = {
                "id": qid,
                "score": score,
                "correct": score >= 70,
                "matched": matched,
                "missing": missing[:8],
                "explanation": q.get("ideal_answer", ""),
                "source_url": q.get("source_url", ""),
                "attribution": q.get("attribution", ""),
            }
        scores.append(score)
        details.append(detail)
    final_score = round(sum(scores) / max(1, len(scores)), 1)
    pass_mark = PASS_MARKS.get(row["difficulty"], 75)
    passed = final_score >= pass_mark
    result = {"score": final_score, "pass_mark": pass_mark, "passed": passed, "details": details}
    with db_connect() as conn:
        conn.execute(
            "UPDATE test_sessions SET result_json=?,score=?,passed=?,completed_at=? WHERE id=?",
            (json.dumps(result), final_score, int(passed), now_iso(), session_id),
        )
    progress_upsert(student_id, "test", row["tool"], "passed" if passed else "needs_review", final_score, f"Difficulty: {row['difficulty']}")
    audit("test_completed", f"tool={row['tool']};score={final_score};passed={passed}", student_id)
    return result


def choose_interview_question(tool: str, difficulty: str, round_name: str, asked: set[str]) -> dict[str, Any] | None:
    pool = [q for q in INTERVIEW_DATA["questions"] if q["id"] not in asked and q["difficulty"] == difficulty and q["round"] == round_name]
    if tool != "full-devops":
        exact = [q for q in pool if q["tool"] == tool]
        if exact:
            pool = exact
    else:
        preferred = [q for q in pool if q["tool"] == "full-devops"]
        if preferred and round_name == "HR & Behavioral":
            pool = preferred
    if not pool:
        pool = [q for q in INTERVIEW_DATA["questions"] if q["id"] not in asked and q["difficulty"] == difficulty and (q["tool"] == tool or tool == "full-devops")]
    return random.choice(pool) if pool else None


def start_interview(student_id: int, tool: str, difficulty: str) -> dict[str, Any]:
    rounds = ["HR & Behavioral", "Technical Fundamentals", "Company Scenario", "Troubleshooting", "Architecture & Trade-offs"]
    if tool != "full-devops":
        rounds = rounds[1:]
    target_questions = 10 if tool == "full-devops" else 8
    first = choose_interview_question(tool, difficulty, rounds[0], set())
    if not first:
        raise ValueError("No interview questions are available.")
    state = {
        "tool": tool,
        "difficulty": difficulty,
        "rounds": rounds,
        "round_index": 0,
        "questions_in_round": 0,
        "target_questions": target_questions,
        "asked_ids": [first["id"]],
        "current_question_id": first["id"],
        "history": [],
        "scores": [],
    }
    sid = "int_" + secrets.token_urlsafe(12)
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO interview_sessions(id,student_id,tool,state_json,created_at) VALUES(?,?,?,?,?)",
            (sid, student_id, tool, json.dumps(state), now_iso()),
        )
    audit("interview_started", f"tool={tool};difficulty={difficulty}", student_id)
    return {"session_id": sid, "round": rounds[0], "difficulty": difficulty, "question": public_question(first), "question_number": 1, "total_questions": target_questions}


def answer_interview(session_id: str, student_id: int, answer: str) -> dict[str, Any]:
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM interview_sessions WHERE id=? AND student_id=?", (session_id, student_id)).fetchone()
    if not row:
        raise ValueError("Interview session was not found.")
    state = json.loads(row["state_json"])
    if row["status"] != "active":
        return {"completed": True, "score": row["score"], "passed": bool(row["passed"]), "history": state.get("history", [])}
    q = INTERVIEW_MAP.get(state["current_question_id"])
    if not q:
        raise ValueError("Current interview question is unavailable.")
    score, matched, missing = score_open_answer(answer, q.get("keywords", []))
    feedback_parts = []
    if score >= 80:
        feedback_parts.append("Strong answer: it covered the main technical and operational expectations.")
    elif score >= 60:
        feedback_parts.append("Acceptable foundation, but the answer needs more evidence, structure, or company-level detail.")
    else:
        feedback_parts.append("The answer is incomplete. Use a structured approach: clarify, diagnose, act safely, validate, communicate, and recover.")
    if missing:
        feedback_parts.append("Consider covering: " + ", ".join(missing[:6]) + ".")
    feedback_parts.append("Reference answer: " + q.get("ideal_answer", ""))
    history_item = {
        "question_id": q["id"], "round": q["round"], "difficulty": q["difficulty"], "question": q["prompt"],
        "answer": answer, "score": score, "matched": matched, "missing": missing[:8], "feedback": " ".join(feedback_parts),
    }
    state["history"].append(history_item)
    state["scores"].append(score)
    state["questions_in_round"] += 1

    # Adaptive level: increase after strong answers, decrease after weak answers.
    idx = LEVELS.index(state["difficulty"]) if state["difficulty"] in LEVELS else 1
    if score >= 82 and idx < len(LEVELS) - 1:
        idx += 1
    elif score < 45 and idx > 0:
        idx -= 1
    state["difficulty"] = LEVELS[idx]

    completed_count = len(state["history"])
    if completed_count >= state["target_questions"]:
        final_score = round(sum(state["scores"]) / max(1, len(state["scores"])), 1)
        passed = final_score >= 70
        with db_connect() as conn:
            conn.execute(
                "UPDATE interview_sessions SET state_json=?,score=?,passed=?,status='completed',completed_at=? WHERE id=?",
                (json.dumps(state), final_score, int(passed), now_iso(), session_id),
            )
        progress_upsert(student_id, "interview", state["tool"], "passed" if passed else "needs_review", final_score, "Adaptive mock interview")
        audit("interview_completed", f"tool={state['tool']};score={final_score};passed={passed}", student_id)
        return {"completed": True, "score": final_score, "passed": passed, "feedback": history_item["feedback"], "history": state["history"]}

    # Two questions per round, then advance.
    if state["questions_in_round"] >= 2:
        state["questions_in_round"] = 0
        state["round_index"] = min(state["round_index"] + 1, len(state["rounds"]) - 1)
    round_name = state["rounds"][state["round_index"]]
    next_q = choose_interview_question(state["tool"], state["difficulty"], round_name, set(state["asked_ids"]))
    if not next_q:
        # Graceful fallback across rounds/difficulties.
        candidates = [x for x in INTERVIEW_DATA["questions"] if x["id"] not in set(state["asked_ids"]) and (x["tool"] == state["tool"] or state["tool"] == "full-devops")]
        next_q = random.choice(candidates) if candidates else None
    if not next_q:
        final_score = round(sum(state["scores"]) / max(1, len(state["scores"])), 1)
        passed = final_score >= 70
        with db_connect() as conn:
            conn.execute("UPDATE interview_sessions SET state_json=?,score=?,passed=?,status='completed',completed_at=? WHERE id=?", (json.dumps(state), final_score, int(passed), now_iso(), session_id))
        return {"completed": True, "score": final_score, "passed": passed, "feedback": history_item["feedback"], "history": state["history"]}
    state["current_question_id"] = next_q["id"]
    state["asked_ids"].append(next_q["id"])
    with db_connect() as conn:
        conn.execute("UPDATE interview_sessions SET state_json=? WHERE id=?", (json.dumps(state), session_id))
    return {
        "completed": False,
        "feedback": history_item["feedback"],
        "answer_score": score,
        "round": next_q["round"],
        "difficulty": state["difficulty"],
        "question": public_question(next_q),
        "question_number": completed_count + 1,
        "total_questions": state["target_questions"],
    }



def import_resume_file(filename: str, encoded: str) -> dict[str, Any]:
    """Extract text from lightweight resume formats without third-party parsers."""
    safe_name = Path(clean_text(filename, 240)).name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in {".docx", ".txt", ".md", ".html", ".htm", ".csv"}:
        raise ValueError("Supported resume imports: DOCX, TXT, Markdown, HTML, and CSV.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("The uploaded resume data is invalid.") from exc
    if len(raw) > 3 * 1024 * 1024:
        raise ValueError("Resume file is larger than the 3 MB local import limit.")
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                xml_data = archive.read("word/document.xml")
            root = ET.fromstring(xml_data)
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            paragraphs = []
            for paragraph in root.iter(namespace + "p"):
                parts = [node.text or "" for node in paragraph.iter(namespace + "t")]
                text = "".join(parts).strip()
                if text:
                    paragraphs.append(text)
            extracted = "\n".join(paragraphs)
        except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
            raise ValueError("The DOCX file could not be read. Confirm that it is a valid Word document.") from exc
    else:
        for encoding in ("utf-8-sig", "utf-16", "cp1252"):
            try:
                extracted = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("The text file encoding could not be recognized.")
        if suffix in {".html", ".htm"}:
            extracted = strip_html(extracted)
    extracted = clean_text(extracted, 50_000)
    if len(extracted) < 20:
        raise ValueError("Very little readable resume text was found in the file.")
    return {"filename": safe_name, "text": extracted, "characters": len(extracted)}

def parse_experience(raw: Any) -> list[dict[str, str]]:
    if isinstance(raw, list):
        result = []
        for item in raw[:12]:
            if isinstance(item, dict):
                result.append({
                    "role": clean_text(item.get("role"), 150),
                    "company": clean_text(item.get("company"), 150),
                    "dates": clean_text(item.get("dates"), 100),
                    "details": clean_text(item.get("details"), 5000),
                })
        return result
    return []


def build_resume(student_id: int, data: dict[str, Any]) -> dict[str, Any]:
    name = clean_text(data.get("name"), 120) or "Candidate Name"
    target_title = clean_text(data.get("target_title"), 150) or "DevOps Engineer"
    contact = clean_text(data.get("contact"), 500)
    summary = clean_text(data.get("summary"), 3000)
    skills = clean_text(data.get("skills"), 4000)
    education = clean_text(data.get("education"), 4000)
    certifications = clean_text(data.get("certifications"), 3000)
    projects = clean_text(data.get("projects"), 6000)
    job_description = clean_text(data.get("job_description"), 20_000)
    existing_resume = clean_text(data.get("existing_resume"), 50_000)
    experience = parse_experience(data.get("experience"))

    jd_keywords = extract_keywords(job_description, 35)
    candidate_text = " ".join([summary, skills, education, certifications, projects, existing_resume] + [" ".join(x.values()) for x in experience])
    candidate_tokens = set(normalize_tokens(candidate_text))
    matched = [k for k in jd_keywords if k in candidate_tokens or k in candidate_text.lower()]
    missing = [k for k in jd_keywords if k not in matched]
    match_score = round(len(matched) / max(1, len(jd_keywords)) * 100, 1) if job_description else 0.0

    lines = [name, target_title]
    if contact:
        lines.append(contact)
    lines.append("")
    if summary:
        lines += ["PROFESSIONAL SUMMARY", summary, ""]
    if skills:
        lines += ["TECHNICAL SKILLS", skills, ""]
    if existing_resume:
        lines += ["IMPORTED RESUME CONTENT", existing_resume, ""]
    if experience:
        lines.append("PROFESSIONAL EXPERIENCE")
        for exp in experience:
            heading = " | ".join(x for x in [exp["role"], exp["company"], exp["dates"]] if x)
            lines.append(heading)
            for bullet in re.split(r"\n+|(?<=\.)\s+(?=[A-Z])", exp["details"]):
                bullet = bullet.strip(" -•\t")
                if bullet:
                    lines.append("• " + bullet)
            lines.append("")
    if projects:
        lines += ["PROJECTS", projects, ""]
    if education:
        lines += ["EDUCATION", education, ""]
    if certifications:
        lines += ["CERTIFICATIONS", certifications, ""]
    text_content = "\n".join(lines).strip() + "\n"

    def section(title: str, content: str) -> str:
        if not content:
            return ""
        return f"<section><h2>{html.escape(title)}</h2><div class='resume-text'>{html.escape(content).replace(chr(10), '<br>')}</div></section>"

    experience_html = ""
    if experience:
        blocks = []
        for exp in experience:
            heading = " | ".join(x for x in [exp["role"], exp["company"], exp["dates"]] if x)
            bullets = [b.strip(" -•\t") for b in re.split(r"\n+|(?<=\.)\s+(?=[A-Z])", exp["details"]) if b.strip(" -•\t")]
            blocks.append(f"<div class='job'><h3>{html.escape(heading)}</h3><ul>{''.join('<li>'+html.escape(b)+'</li>' for b in bullets)}</ul></div>")
        experience_html = "<section><h2>Professional Experience</h2>" + "".join(blocks) + "</section>"
    html_content = f"""<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(name)} Resume</title>
<style>body{{font-family:Arial,Helvetica,sans-serif;max-width:850px;margin:36px auto;color:#111;line-height:1.45}}h1{{margin:0;font-size:30px}}.title{{font-size:18px;margin-top:3px}}.contact{{margin:8px 0 20px}}h2{{font-size:15px;text-transform:uppercase;border-bottom:1px solid #222;padding-bottom:4px;margin:22px 0 8px}}h3{{font-size:14px;margin:10px 0 4px}}ul{{margin-top:4px}}.resume-text{{white-space:normal}}@media print{{body{{margin:0.45in}}}}</style></head><body>
<header><h1>{html.escape(name)}</h1><div class='title'>{html.escape(target_title)}</div><div class='contact'>{html.escape(contact)}</div></header>
{section('Professional Summary', summary)}{section('Technical Skills', skills)}{section('Imported Resume Content', existing_resume)}{experience_html}{section('Projects', projects)}{section('Education', education)}{section('Certifications', certifications)}
</body></html>"""
    rid = "resume_" + secrets.token_urlsafe(10)
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO resumes(id,student_id,title,text_content,html_content,match_score,missing_keywords,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (rid, student_id, f"{name} - {target_title}", text_content, html_content, match_score, json.dumps(missing[:25]), now_iso()),
        )
    audit("resume_generated", f"title={target_title};match_score={match_score}", student_id)
    return {
        "id": rid, "title": f"{name} - {target_title}", "text": text_content, "html": html_content,
        "match_score": match_score, "matched_keywords": matched, "missing_keywords": missing[:25],
        "notice": "The builder never invents qualifications. Review every statement for accuracy before submitting the resume.",
    }


def strip_html(raw: str) -> str:
    text = re.sub(r"<pre><code>(.*?)</code></pre>", lambda m: " CODE " + re.sub(r"<[^>]+>", " ", m.group(1)) + " ", raw, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def sync_stackexchange(tool: str, tag: str, limit: int = 8) -> dict[str, Any]:
    tag = re.sub(r"[^a-zA-Z0-9+.#_-]", "", tag)[:40] or tool
    params = urllib.parse.urlencode({
        "site": "stackoverflow", "tagged": tag, "sort": "votes", "order": "desc", "pagesize": min(max(limit * 3, 10), 40), "filter": "withbody"
    })
    url = "https://api.stackexchange.com/2.3/questions?" + params
    req = urllib.request.Request(url, headers={"User-Agent": f"BillingerBot/{VERSION} local-learning-app"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError(f"Online sync failed: {exc}") from exc
    questions = [q for q in payload.get("items", []) if q.get("accepted_answer_id")][:limit]
    if not questions:
        return {"imported": 0, "message": "No accepted-answer questions were returned for this tag."}
    answer_ids = [str(q["accepted_answer_id"]) for q in questions]
    answer_url = "https://api.stackexchange.com/2.3/answers/" + ";".join(answer_ids) + "?" + urllib.parse.urlencode({"site": "stackoverflow", "filter": "withbody"})
    req2 = urllib.request.Request(answer_url, headers={"User-Agent": f"BillingerBot/{VERSION} local-learning-app"})
    try:
        with urllib.request.urlopen(req2, timeout=20) as resp:
            answer_payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError(f"Accepted-answer sync failed: {exc}") from exc
    answers = {a["answer_id"]: a for a in answer_payload.get("items", [])}
    imported = 0
    with db_connect() as conn:
        for q in questions:
            answer = answers.get(q["accepted_answer_id"])
            if not answer:
                continue
            title = html.unescape(q.get("title", "Stack Overflow question"))
            body = strip_html(q.get("body", ""))[:2500]
            ideal = strip_html(answer.get("body", ""))[:5000]
            if len(ideal) < 80:
                continue
            keywords = list(dict.fromkeys((q.get("tags") or []) + extract_keywords(ideal, 18)))[:20]
            q_owner = html.unescape((q.get("owner") or {}).get("display_name", "community member"))
            a_owner = html.unescape((answer.get("owner") or {}).get("display_name", "community member"))
            attribution = f"Stack Overflow question by {q_owner}; accepted answer by {a_owner}. Follow the source link for full attribution and license details."
            oid = "online_so_" + str(q["question_id"])
            prompt = f"Internet-sourced scenario: {title}\n\n{body}\n\nExplain the correct diagnosis or solution in your own words."
            conn.execute(
                """
                INSERT INTO online_questions(id,tool,difficulty,prompt,keywords,ideal_answer,source_url,source_title,attribution,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET tool=excluded.tool,difficulty=excluded.difficulty,prompt=excluded.prompt,keywords=excluded.keywords,
                ideal_answer=excluded.ideal_answer,source_url=excluded.source_url,source_title=excluded.source_title,attribution=excluded.attribution,created_at=excluded.created_at
                """,
                (oid, tool, "Intermediate", prompt, json.dumps(keywords), ideal, q.get("link", ""), title, attribution, now_iso()),
            )
            imported += 1
    audit("online_questions_synced", f"tool={tool};tag={tag};imported={imported}")
    return {"imported": imported, "tag": tag, "message": f"Imported {imported} attributed questions with accepted answers."}


class AppHandler(BaseHTTPRequestHandler):
    server_version = "BillingerLocal/2.6"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), geolocation=(), payment=(), usb=(), serial=()")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("X-Permitted-Cross-Domain-Policies", "none")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-src 'self';")
        super().end_headers()

    def send_json(self, data: Any, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def send_error_json(self, message: str, status: int = 400) -> None:
        self.send_json({"error": message}, status)

    def send_local_file(self, path: Path, mime: str, filename: str, inline: bool = False) -> None:
        content = path.read_bytes()
        disposition = "inline" if inline else "attachment"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Disposition", f'{disposition}; filename="{filename}"')
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "private, max-age=300")
        self.end_headers()
        self.wfile.write(content)

    def read_json(self) -> dict[str, Any]:
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError:
            raise ValueError("Invalid Content-Length")
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("Request body is too large")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def parse(self) -> tuple[str, dict[str, list[str]]]:
        parsed = urllib.parse.urlparse(self.path)
        return parsed.path, urllib.parse.parse_qs(parsed.query)

    def admin_token(self) -> str:
        return clean_text(self.headers.get("X-Admin-Token", ""), 200)

    def require_admin(self) -> None:
        v23.require_admin(self.admin_token())

    def student_token(self) -> str:
        return clean_text(self.headers.get("X-Student-Token", ""), 300)

    def require_student(self, student_id: int) -> None:
        v24.require_student(self.student_token(), student_id)

    def validate_local_request(self, require_origin: bool = False) -> None:
        host = (self.headers.get("Host") or "").lower().strip()
        host_name = host.rsplit(":", 1)[0].strip("[]") if host else ""
        if host_name not in {"127.0.0.1", "localhost", "::1"}:
            raise PermissionError("This local server accepts only localhost requests.")
        origin = (self.headers.get("Origin") or "").strip()
        if origin:
            parsed = urllib.parse.urlparse(origin)
            if parsed.scheme != "http" or (parsed.hostname or "").lower() not in {"127.0.0.1", "localhost", "::1"}:
                raise PermissionError("Cross-origin requests are blocked.")
        elif require_origin and (self.headers.get("Sec-Fetch-Site") or "").lower() == "cross-site":
            raise PermissionError("Cross-site requests are blocked.")

    def serve_static(self, path: str) -> None:
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        candidate = (STATIC_DIR / rel).resolve()
        if STATIC_DIR.resolve() not in candidate.parents and candidate != STATIC_DIR.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not candidate.is_file():
            # SPA fallback for client-side navigation.
            candidate = STATIC_DIR / "index.html"
        content = candidate.read_bytes()
        mime, _ = mimetypes.guess_type(candidate.name)
        self.send_response(200)
        self.send_header("Content-Type", (mime or "application/octet-stream") + ("; charset=utf-8" if (mime or "").startswith(("text/", "application/javascript")) else ""))
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        path, query = self.parse()
        try:
            self.validate_local_request(False)
            if path == "/oauth/gmail/callback":
                code = clean_text((query.get("code") or [""])[0], 3000)
                state_value = clean_text((query.get("state") or [""])[0], 300)
                if not code or not state_value:
                    raise ValueError("Gmail OAuth callback is missing code or state.")
                result = v24.gmail_oauth_callback(code, state_value)
                content = ("<!doctype html><html><head><meta charset='utf-8'><title>Gmail connected</title>"
                           "<style>body{font:16px system-ui;background:#07111e;color:#dff;padding:50px;text-align:center}"
                           ".card{max-width:600px;margin:auto;padding:36px;border:1px solid #22d3ee66;border-radius:24px;background:#0f172a}</style></head>"
                           f"<body><div class='card'><h1>Gmail connected</h1><p>Student profile {result['student_id']} can now send approved application drafts.</p><p>Return to Billinger Bot and refresh Career Command.</p></div></body></html>").encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(content))); self.end_headers(); self.wfile.write(content); return
            if path == "/api/v7/readiness":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                return self.send_json(v27.readiness_status(sid, len(RESOURCE_INDEX.get("resources", [])), v23.admin_status().get("configured", False)))
            if path == "/api/v7/mastery":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                return self.send_json(v27.mastery_gates(sid))
            if path == "/api/v7/graduation":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                return self.send_json(v27.graduation_summary(sid))
            if path == "/api/v7/environment":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                latest = v27.latest_environment(sid)
                return self.send_json(latest or {"results": None})
            if path == "/api/v7/backup/health":
                self.require_admin(); return self.send_json(v27.backup_health())
            if path == "/api/v7/freshness":
                return self.send_json(v27.freshness_dashboard())
            if path == "/api/v7/ai/models":
                self.require_admin(); return self.send_json(v26.model_cache(clean_text((query.get("provider") or [""])[0],40)))
            if path == "/api/v6/ai/dashboard":
                self.require_admin(); return self.send_json(v26.dashboard())
            if path == "/api/v6/ai/status":
                return self.send_json(v26.student_status())
            if path == "/api/v6/ai/analyses":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                return self.send_json(v26.recent_student_analyses(sid, int((query.get("limit") or ["20"])[0])))
            if path == "/api/v4/career/dashboard":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                return self.send_json(v24.career_dashboard(sid))
            if path == "/api/v4/job":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                return self.send_json(v24.get_job(sid, clean_text((query.get("id") or [""])[0], 100)))
            if path == "/api/v4/portfolio/file":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                fpath, mime, filename, inline = v24.portfolio_file(sid, clean_text((query.get("id") or [""])[0],100), clean_text((query.get("format") or ["html"])[0],10))
                return self.send_local_file(fpath, mime.split(";")[0], re.sub(r"[^A-Za-z0-9._-]", "_", filename), inline)
            if path == "/api/v4/resume/file":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                fpath, mime, filename, inline = v24.resume_variant_file(sid, clean_text((query.get("id") or [""])[0],100), clean_text((query.get("format") or ["pdf"])[0],10))
                return self.send_local_file(fpath, mime.split(";")[0], re.sub(r"[^A-Za-z0-9._-]", "_", filename), inline)
            if path == "/api/v4/email/file":
                sid = int((query.get("student_id") or ["0"])[0]); self.require_student(sid)
                fpath, mime, filename, inline = v24.email_draft_file(sid, clean_text((query.get("id") or [""])[0],100))
                return self.send_local_file(fpath, mime, re.sub(r"[^A-Za-z0-9._-]", "_", filename), inline)
            if path == "/api/v4/requirements":
                return self.send_json(v24.system_requirements())
            if path == "/api/resources":
                tool = clean_text((query.get("tool") or [""])[0], 100)
                collection = clean_text((query.get("collection") or [""])[0], 30)
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json(list_learning_resources(tool, student_id, collection))
            if path == "/api/resource":
                resource_id = clean_text((query.get("id") or [""])[0], 100)
                return self.send_json(read_learning_resource(resource_id))
            if path == "/api/resource/file":
                resource_id = clean_text((query.get("id") or [""])[0], 100)
                fmt = clean_text((query.get("format") or ["pdf"])[0], 10).lower()
                resource = RESOURCE_MAP.get(resource_id)
                if not resource:
                    return self.send_error_json("Learning resource not found", 404)
                if fmt == "docx":
                    rel = resource.get("docx_file")
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    inline = False
                else:
                    rel = resource.get("pdf_file")
                    mime = "application/pdf"
                    inline = True
                if not rel:
                    return self.send_error_json(f"{fmt.upper()} version is unavailable for this resource", 404)
                candidate = (LEARNING_RESOURCE_DIR / rel).resolve()
                if LEARNING_RESOURCE_DIR.resolve() not in candidate.parents or not candidate.is_file():
                    return self.send_error_json("Learning resource file is unavailable", 404)
                return self.send_local_file(candidate, mime, candidate.name, inline)
            if path == "/api/v3/status":
                return self.send_json({"version": VERSION, "admin": v23.admin_status(), "storage": v23.storage_usage(), "roles": v23.ROLE_TRACKS})
            if path == "/api/v3/student/hub":
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json(v23.student_hub(student_id))
            if path == "/api/v3/roadmap":
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json(v23.dependency_roadmap(student_id))
            if path == "/api/v3/practical/templates":
                tool = clean_text((query.get("tool") or [""])[0], 80)
                level = clean_text((query.get("level") or [""])[0], 30)
                return self.send_json({"templates": v23.practical_exam_templates(tool, level)})
            if path == "/api/v3/workspace":
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json(v23.list_workspace(student_id))
            if path == "/api/v3/workspace/file":
                student_id = int((query.get("student_id") or ["0"])[0])
                rel = clean_text((query.get("path") or [""])[0], 240)
                candidate, content = v23.read_workspace_file(student_id, rel)
                mime, _ = mimetypes.guess_type(candidate.name)
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{candidate.name}"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers(); self.wfile.write(content); return
            if path == "/api/v3/certificates":
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json({"certificates": v23.list_certificates(student_id)})
            if path == "/api/v3/certificate/file":
                certificate_id = clean_text((query.get("id") or [""])[0], 100)
                file_name, content = v23.certificate_file(certificate_id)
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{file_name}"')
                self.send_header("Content-Length", str(len(content))); self.end_headers(); self.wfile.write(content); return
            if path == "/api/v3/certificate/verify":
                code = clean_text((query.get("code") or [""])[0], 60)
                return self.send_json(v23.verify_certificate(code))
            if path == "/api/v3/admin/overview":
                self.require_admin(); return self.send_json(v23.admin_overview())
            if path == "/api/v3/admin/import":
                self.require_admin(); import_id = clean_text((query.get("id") or [""])[0], 100)
                return self.send_json(v23.get_content_import(import_id))
            if path == "/api/v3/admin/content/versions":
                self.require_admin(); return self.send_json({"versions": v23.list_content_versions()})
            if path == "/api/v3/admin/backups":
                self.require_admin(); return self.send_json({"backups": v23.list_backups(), "updates": v23.list_updates()})
            if path == "/api/v3/admin/report.csv":
                self.require_admin(); content = v23.admin_report_csv()
                self.send_response(200); self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="Billinger_Student_Report.csv"')
                self.send_header("Content-Length", str(len(content))); self.end_headers(); self.wfile.write(content); return
            if path == "/api/v3/backup/file":
                self.require_admin(); backup_id = clean_text((query.get("id") or [""])[0], 120)
                file_name, content = v23.backup_file(backup_id)
                self.send_response(200); self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{file_name}"')
                self.send_header("Content-Length", str(len(content))); self.end_headers(); self.wfile.write(content); return
            if path == "/api/v2/company":
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json(v2.company_overview(student_id))
            if path == "/api/v2/skills":
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json(v2.skill_matrix(student_id))
            if path == "/api/v2/readiness":
                return self.send_json(v2.system_readiness())
            if path == "/api/v2/settings":
                return self.send_json(v2.get_settings())
            if path == "/api/v2/capstones":
                return self.send_json(v2.capstones())
            if path == "/api/v2/coverage":
                return self.send_json(build_coverage_catalog())
            if path == "/api/health":
                ready = v2.system_readiness()
                return self.send_json({"status": "ok", "app": APP_NAME, "version": VERSION, "local_only": True, "capabilities": {"company_simulation": True, "safe_labs": True, "recruitment_journey": True, "skill_matrix": True, "local_ai_connector": True, "multi_provider_ai": True, "automatic_ai_failover": True, "ai_test_analysis": True, "ai_interview_analysis": True, "ai_curriculum_auditor": True, "learning_library": True, "document_qa": True, "training_institute": True, "admin_portal": True, "practical_exams": True, "project_workspaces": True, "certificates": True, "verified_importer": True, "offline_updates": True, "career_command": True, "portfolio_builder": True, "truthful_resume_tailoring": True, "approved_email_workflow": True, "job_specific_interviews": True}, "runtime": {"python": ready["python"], "os": ready["os"]}})
            if path == "/api/students":
                with db_connect() as conn:
                    rows = conn.execute("SELECT id,name,email,active,created_at,last_active,(pin_hash!='') AS pin_protected FROM students WHERE active=1 ORDER BY id").fetchall()
                return self.send_json({"students": [json_safe_row(r) for r in rows], "max_students": MAX_STUDENTS})
            if path == "/api/catalog":
                summaries = []
                for t in CATALOG["tools"]:
                    summaries.append({k: t[k] for k in ("slug", "name", "category", "icon", "description", "why_company", "order")})
                return self.send_json({"track": CATALOG["track"], "version": CATALOG["version"], "tools": summaries})
            if path == "/api/tool":
                slug = clean_text((query.get("slug") or [""])[0], 100)
                tool = TOOL_MAP.get(slug)
                if not tool:
                    return self.send_error_json("Tool not found", 404)
                return self.send_json(tool)
            if path == "/api/progress":
                student_id = int((query.get("student_id") or ["0"])[0])
                with db_connect() as conn:
                    rows = conn.execute("SELECT item_type,item_id,status,score,attempts,notes,updated_at FROM progress WHERE student_id=?", (student_id,)).fetchall()
                return self.send_json({"progress": [json_safe_row(r) for r in rows], "stats": student_stats(student_id)})
            if path == "/api/stats":
                student_id = int((query.get("student_id") or ["0"])[0])
                return self.send_json(student_stats(student_id))
            if path == "/api/resumes":
                student_id = int((query.get("student_id") or ["0"])[0])
                with db_connect() as conn:
                    rows = conn.execute("SELECT id,title,match_score,missing_keywords,created_at FROM resumes WHERE student_id=? ORDER BY created_at DESC", (student_id,)).fetchall()
                items = []
                for r in rows:
                    item = json_safe_row(r)
                    item["missing_keywords"] = json.loads(item["missing_keywords"])
                    items.append(item)
                return self.send_json({"resumes": items})
            if path == "/api/resume/download":
                rid = clean_text((query.get("id") or [""])[0], 100)
                fmt = clean_text((query.get("format") or ["html"])[0], 20).lower()
                with db_connect() as conn:
                    row = conn.execute("SELECT * FROM resumes WHERE id=?", (rid,)).fetchone()
                if not row:
                    return self.send_error_json("Resume not found", 404)
                if fmt == "txt":
                    content = row["text_content"].encode("utf-8")
                    filename = "ATS_Resume.txt"
                    mime = "text/plain; charset=utf-8"
                elif fmt == "doc":
                    content = row["html_content"].encode("utf-8")
                    filename = "ATS_Resume.doc"
                    mime = "application/msword"
                else:
                    content = row["html_content"].encode("utf-8")
                    filename = "ATS_Resume.html"
                    mime = "text/html; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            if path == "/api/history":
                student_id = int((query.get("student_id") or ["0"])[0])
                with db_connect() as conn:
                    rows = conn.execute("SELECT action,detail,created_at FROM audit_log WHERE student_id=? OR student_id IS NULL ORDER BY id DESC LIMIT 100", (student_id,)).fetchall()
                return self.send_json({"history": [json_safe_row(r) for r in rows]})
            if path == "/api/backup":
                with db_connect() as conn:
                    tables = ["students", "progress", "practice_submissions", "test_sessions", "interview_sessions", "resumes", "online_questions", "audit_log", *v2.v2_backup_tables(), *v26.backup_tables(), *v27.backup_tables()]
                    payload = {"app": APP_NAME, "version": VERSION, "created_at": now_iso(), "tables": {}}
                    for table in tables:
                        payload["tables"][table] = [json_safe_row(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
                raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="billinger_backup.json"')
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if path.startswith("/api/"):
                return self.send_error_json("API endpoint not found", 404)
            return self.serve_static(path)
        except PermissionError as exc:
            self.send_error_json(str(exc), 403)
        except (ValueError, TypeError, sqlite3.Error) as exc:
            self.send_error_json(str(exc), 400)
        except Exception as exc:  # Prevent raw tracebacks from leaking to browser.
            audit("server_error", repr(exc))
            self.send_error_json("Unexpected local server error. Check the console log.", 500)

    def do_POST(self) -> None:
        path, _ = self.parse()
        try:
            self.validate_local_request(True)
            data = self.read_json()
            if path == "/api/v7/readiness/seen":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v27.mark_wizard_seen(sid))
            if path == "/api/v7/baseline/start":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v27.start_baseline(sid))
            if path == "/api/v7/baseline/submit":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v27.submit_baseline(sid,clean_text(data.get("session_id"),120),data.get("answers",[])))
            if path == "/api/v7/environment/check":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v27.check_environment(sid))
            if path == "/api/v7/freshness/save":
                self.require_admin(); return self.send_json(v27.save_freshness(data))
            if path == "/api/v7/ai/models/discover":
                self.require_admin(); return self.send_json(v26.discover_models(clean_text(data.get("provider"),40)))
            if path == "/api/v7/ai/fallback/dry-run":
                self.require_admin(); return self.send_json(v26.fallback_chain_dry_run(clean_text(data.get("task"),60),data.get("simulated_failures",[])))
            if path == "/api/v6/ai/provider/save":
                self.require_admin(); return self.send_json(v26.save_provider(data))
            if path == "/api/v6/ai/provider/test":
                self.require_admin(); return self.send_json(v26.test_provider(clean_text(data.get("provider"),40)))
            if path == "/api/v6/ai/route/save":
                self.require_admin(); return self.send_json(v26.save_task_route(clean_text(data.get("task"),60), data.get("providers",[])))
            if path == "/api/v6/ai/settings/save":
                self.require_admin(); return self.send_json(v26.save_settings(data))
            if path == "/api/v6/ai/chat":
                sid=int(data.get("student_id",0)); self.require_student(sid)
                return self.send_json(v26.tutor_chat(sid, data.get("messages",[]), clean_text(data.get("context"),40000)))
            if path == "/api/v6/ai/test/analyze":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v26.analyze_test(sid,data))
            if path == "/api/v6/ai/interview/analyze":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v26.analyze_interview(sid,data))
            if path == "/api/v6/ai/questions/generate":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v26.generate_question_set(sid,data))
            if path == "/api/v6/ai/questions/submit":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v26.grade_question_set(sid,clean_text(data.get("session_id"),120),data.get("answers",[])))
            if path == "/api/v6/ai/curriculum/audit":
                self.require_admin(); return self.send_json(v26.curriculum_audit(None,data))
            if path == "/api/v4/student/session":
                return self.send_json(v24.create_student_session(int(data.get("student_id",0)), clean_text(data.get("pin"),30), verify_pin))
            if path == "/api/v4/profile/save":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.save_candidate_profile(sid,data))
            if path == "/api/v4/source/add":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.add_job_source(sid,clean_text(data.get("source_type"),30),clean_text(data.get("name"),160),clean_text(data.get("identifier"),1000)))
            if path == "/api/v4/source/scan":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.scan_job_sources(sid,clean_text(data.get("source_id"),100)))
            if path == "/api/v4/job/analyze":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.analyze_manual_job(sid,data))
            if path == "/api/v4/job/status":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.save_job_status(sid,clean_text(data.get("job_id"),100),clean_text(data.get("status"),40)))
            if path == "/api/v4/portfolio/project/save":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.save_portfolio_project(sid,data))
            if path == "/api/v4/portfolio/build":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.generate_portfolio(sid,data))
            if path == "/api/v4/resume/generate":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.generate_tailored_resume(sid,clean_text(data.get("job_id"),100),clean_text(data.get("portfolio_build_id"),100)))
            if path == "/api/v4/email/draft":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.create_email_draft(sid,data))
            if path == "/api/v4/gmail/client":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.save_gmail_client(sid,clean_text(data.get("filename"),240),clean_text(data.get("content_base64"),400000)))
            if path == "/api/v4/gmail/auth/start":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.gmail_auth_start(sid,clean_text(data.get("redirect_uri"),500)))
            if path == "/api/v4/email/send":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.send_email_draft(sid,clean_text(data.get("draft_id"),100),clean_text(data.get("confirmation"),20)))
            if path == "/api/v4/application/assisted":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.mark_assisted_application(sid,clean_text(data.get("job_id"),100),clean_text(data.get("resume_variant_id"),100),clean_text(data.get("portfolio_build_id"),100),clean_text(data.get("notes"),4000)))
            if path == "/api/v4/research":
                sid=int(data.get("student_id",0)); self.require_student(sid); return self.send_json(v24.research_and_prepare_interview(sid,clean_text(data.get("job_id"),100),clean_text(data.get("company_url"),1000)))
            if path == "/api/v3/admin/setup":
                return self.send_json(v23.admin_setup(clean_text(data.get("pin"), 30), clean_text(data.get("admin_name"), 120), clean_text(data.get("institute_name"), 160)))
            if path == "/api/v3/admin/auth":
                return self.send_json(v23.admin_auth(clean_text(data.get("pin"), 30)))
            if path == "/api/v3/admin/settings":
                self.require_admin(); return self.send_json(v23.save_institute_settings(data))
            if path == "/api/v3/admin/batch/save":
                self.require_admin(); return self.send_json(v23.save_batch(data))
            if path == "/api/v3/admin/batch/member":
                self.require_admin(); return self.send_json(v23.assign_batch_member(int(data.get("batch_id",0)), int(data.get("student_id",0)), bool(data.get("assigned",True))))
            if path == "/api/v3/admin/student/update":
                self.require_admin(); return self.send_json(v23.update_student(data))
            if path == "/api/v3/admin/assignment/create":
                self.require_admin(); return self.send_json(v23.create_assignment(data))
            if path == "/api/v3/admin/announcement/create":
                self.require_admin(); return self.send_json(v23.create_announcement(data))
            if path == "/api/v3/admin/import/stage":
                self.require_admin(); return self.send_json(v23.stage_content_import(clean_text(data.get("filename"),240), clean_text(data.get("content_base64"),105_000_000)))
            if path == "/api/v3/admin/import/publish":
                self.require_admin(); result=v23.publish_content_import(clean_text(data.get("import_id"),100), data.get("mappings",[])); reload_resource_index(); return self.send_json(result)
            if path == "/api/v3/admin/backup/create":
                self.require_admin(); return self.send_json(v23.create_backup())
            if path == "/api/v3/admin/restore/stage":
                self.require_admin(); return self.send_json(v23.stage_restore(clean_text(data.get("filename"),240), clean_text(data.get("content_base64"),105_000_000)))
            if path == "/api/v3/admin/update/stage":
                self.require_admin(); return self.send_json(v23.stage_offline_update(clean_text(data.get("filename"),240), clean_text(data.get("content_base64"),105_000_000)))
            if path == "/api/v3/profile/save":
                return self.send_json(v23.update_student(data))
            if path == "/api/v3/plan/generate":
                return self.send_json(v23.generate_daily_plan(int(data.get("student_id",0)), clean_text(data.get("date"),20)))
            if path == "/api/v3/practical/start":
                return self.send_json(v23.start_practical_exam(int(data.get("student_id",0)), clean_text(data.get("exam_code"),100)))
            if path == "/api/v3/practical/submit":
                return self.send_json(v23.submit_practical_exam(clean_text(data.get("run_id"),100), int(data.get("student_id",0)), clean_text(data.get("response"),60000)))
            if path == "/api/v3/workspace/save":
                return self.send_json(v23.save_workspace_file(int(data.get("student_id",0)), clean_text(data.get("path"),240), clean_text(data.get("content"),2_000_000), clean_text(data.get("tool"),80)))
            if path == "/api/v3/workspace/upload":
                return self.send_json(v23.upload_workspace_file(int(data.get("student_id",0)), clean_text(data.get("path"),240), clean_text(data.get("content_base64"),12_000_000), clean_text(data.get("tool"),80)))
            if path == "/api/v3/certificate/issue":
                self.require_admin(); return self.send_json(v23.issue_certificate(int(data.get("student_id",0)), clean_text(data.get("certificate_type"),80), clean_text(data.get("subject"),180), float(data.get("score",0))))
            if path == "/api/resource/ask":
                sid = int(data.get("student_id", 0))
                resource_id = clean_text(data.get("resource_id"), 100)
                question = clean_text(data.get("question"), 2000)
                result = answer_from_learning_resource(resource_id, question)
                audit("learning_resource_question", f"resource={resource_id};mode={result['mode']};question={question[:180]}", sid if student_exists(sid) else None)
                return self.send_json(result)
            if path == "/api/resource/progress":
                sid = int(data.get("student_id", 0))
                resource_id = clean_text(data.get("resource_id"), 100)
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                if resource_id not in RESOURCE_MAP:
                    raise ValueError("Learning resource not found.")
                completed = bool(data.get("completed", True))
                progress_upsert(sid, "resource", resource_id, "completed" if completed else "in_progress", 100 if completed else 0, "Course book review status")
                audit("learning_resource_progress", f"resource={resource_id};completed={completed}", sid)
                return self.send_json({"resource_id": resource_id, "status": "completed" if completed else "in_progress"})
            if path == "/api/v2/company/ticket/submit":
                sid = int(data.get("student_id", 0))
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                return self.send_json(v2.submit_ticket(sid, clean_text(data.get("ticket_id"), 100), clean_text(data.get("response"), 40000), clean_text(data.get("standup"), 8000)))
            if path == "/api/v2/company/incident/submit":
                sid = int(data.get("student_id", 0))
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                return self.send_json(v2.submit_incident(sid, clean_text(data.get("incident_id"), 100), clean_text(data.get("response"), 40000)))
            if path == "/api/v2/lab/run":
                sid = int(data.get("student_id", 0))
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                return self.send_json(v2.run_lab_command(sid, clean_text(data.get("command"), 500), clean_text(data.get("mode"), 30) or None))
            if path == "/api/v2/capstone/submit":
                sid = int(data.get("student_id", 0))
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                return self.send_json(v2.submit_capstone(sid, clean_text(data.get("capstone_id"), 100), clean_text(data.get("submission"), 80000)))
            if path == "/api/v2/recruitment/start":
                sid = int(data.get("student_id", 0))
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                track = clean_text(data.get("track"), 100) or "full-devops"
                if track not in TOOL_MAP and track != "full-devops":
                    raise ValueError("Invalid recruitment track.")
                return self.send_json(v2.start_recruitment(sid, clean_text(data.get("target_role"), 160), track, clean_text(data.get("difficulty"), 30), clean_text(data.get("resume_text"), 80000), clean_text(data.get("job_description"), 80000)))
            if path == "/api/v2/recruitment/answer":
                sid = int(data.get("student_id", 0))
                return self.send_json(v2.answer_recruitment(clean_text(data.get("session_id"), 120), sid, clean_text(data.get("answer"), 30000)))
            if path == "/api/v2/settings":
                return self.send_json(v2.save_settings(data))
            if path == "/api/v2/ai/chat":
                messages = data.get("messages", [])
                if not isinstance(messages, list) or not messages:
                    raise ValueError("Messages are required.")
                safe_messages = []
                for msg in messages[-12:]:
                    if isinstance(msg, dict) and msg.get("role") in {"user", "assistant"}:
                        safe_messages.append({"role": msg["role"], "content": clean_text(msg.get("content"), 12000)})
                return self.send_json(v2.local_ai_chat(safe_messages, clean_text(data.get("purpose"), 50) or "coach"))
            if path == "/api/students":
                name = clean_text(data.get("name"), 120)
                email = clean_text(data.get("email"), 200)
                pin = clean_text(data.get("pin"), 30)
                if len(name) < 2:
                    raise ValueError("Student name is required.")
                with db_connect() as conn:
                    count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
                    if count >= MAX_STUDENTS:
                        raise ValueError(f"The local edition supports up to {MAX_STUDENTS} student profiles.")
                    ts = now_iso()
                    cur = conn.execute("INSERT INTO students(name,email,pin_hash,created_at,last_active) VALUES(?,?,?,?,?)", (name, email, hash_pin(pin), ts, ts))
                    sid = cur.lastrowid
                audit("student_created", name, sid)
                return self.send_json({"id": sid, "name": name}, 201)
            if path == "/api/students/auth":
                sid = int(data.get("student_id", 0))
                pin = clean_text(data.get("pin"), 30)
                with db_connect() as conn:
                    row = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
                    if not row or not verify_pin(pin, row["pin_hash"]):
                        return self.send_error_json("Invalid student or PIN", 401)
                    conn.execute("UPDATE students SET last_active=? WHERE id=?", (now_iso(), sid))
                return self.send_json({"authenticated": True, "student": {"id": row["id"], "name": row["name"], "email": row["email"]}})
            if path == "/api/progress/lesson":
                sid = int(data.get("student_id", 0))
                lesson_id = clean_text(data.get("lesson_id"), 100)
                if not student_exists(sid) or lesson_id not in LESSON_MAP:
                    raise ValueError("Invalid student or lesson.")
                status = "completed" if data.get("completed", True) else "in_progress"
                progress_upsert(sid, "lesson", lesson_id, status, 100 if status == "completed" else 0, clean_text(data.get("notes"), 2000))
                audit("lesson_progress", f"{lesson_id}:{status}", sid)
                return self.send_json({"saved": True, "stats": student_stats(sid)})
            if path == "/api/practice/submit":
                sid = int(data.get("student_id", 0))
                lab_id = clean_text(data.get("lab_id"), 100)
                response = clean_text(data.get("response"), 30_000)
                if not student_exists(sid) or lab_id not in LAB_MAP:
                    raise ValueError("Invalid student or lab.")
                if len(response) < 40:
                    raise ValueError("Practice response is too short. Include your plan, actions, evidence, and rollback.")
                lab = LAB_MAP[lab_id]
                score, matched, missing = score_open_answer(response, lab.get("keywords", []))
                passed = score >= 70
                feedback = ("Passed. " if passed else "Needs improvement. ") + f"Matched: {', '.join(matched[:8]) or 'none'}. " + (f"Add coverage for: {', '.join(missing[:8])}. " if missing else "") + "Use concrete commands/configuration, validation evidence, risk controls, and rollback."
                with db_connect() as conn:
                    conn.execute("INSERT INTO practice_submissions(student_id,lab_id,response,score,feedback,created_at) VALUES(?,?,?,?,?,?)", (sid, lab_id, response, score, feedback, now_iso()))
                progress_upsert(sid, "lab", lab_id, "passed" if passed else "needs_review", score, feedback)
                audit("practice_submitted", f"lab={lab_id};score={score}", sid)
                return self.send_json({"score": score, "passed": passed, "feedback": feedback, "matched": matched, "missing": missing[:10]})
            if path == "/api/test/start":
                sid = int(data.get("student_id", 0))
                tool = clean_text(data.get("tool"), 100) or "linux"
                difficulty = clean_text(data.get("difficulty"), 30) or "Beginner"
                count = int(data.get("count", 8))
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                if tool not in TOOL_MAP and tool != "full-devops":
                    raise ValueError("Invalid tool.")
                if difficulty not in LEVELS:
                    raise ValueError("Invalid difficulty.")
                return self.send_json(build_test(sid, tool, difficulty, count, bool(data.get("include_online", False))))
            if path == "/api/test/submit":
                sid = int(data.get("student_id", 0))
                session_id = clean_text(data.get("session_id"), 100)
                answers = data.get("answers", [])
                if not isinstance(answers, list):
                    raise ValueError("Answers must be a list.")
                return self.send_json(grade_test(session_id, sid, answers))
            if path == "/api/interview/start":
                sid = int(data.get("student_id", 0))
                tool = clean_text(data.get("tool"), 100) or "full-devops"
                difficulty = clean_text(data.get("difficulty"), 30) or "Intermediate"
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                if tool not in TOOL_MAP and tool != "full-devops":
                    raise ValueError("Invalid interview track.")
                if difficulty not in LEVELS:
                    raise ValueError("Invalid difficulty.")
                return self.send_json(start_interview(sid, tool, difficulty))
            if path == "/api/interview/answer":
                sid = int(data.get("student_id", 0))
                session_id = clean_text(data.get("session_id"), 100)
                answer = clean_text(data.get("answer"), 30_000)
                if len(answer) < 10:
                    raise ValueError("Provide a fuller interview answer.")
                return self.send_json(answer_interview(session_id, sid, answer))
            if path == "/api/resume/import":
                filename = clean_text(data.get("filename"), 240)
                encoded = clean_text(data.get("content_base64"), 4_500_000)
                if not filename or not encoded:
                    raise ValueError("Resume filename and file content are required.")
                return self.send_json(import_resume_file(filename, encoded))
            if path == "/api/resume/generate":
                sid = int(data.get("student_id", 0))
                if not student_exists(sid):
                    raise ValueError("Student not found.")
                return self.send_json(build_resume(sid, data))
            if path == "/api/online/sync":
                tool = clean_text(data.get("tool"), 100) or "full-devops"
                tag = clean_text(data.get("tag"), 50) or ("devops" if tool == "full-devops" else tool)
                limit = int(data.get("limit", 8))
                if tool not in TOOL_MAP and tool != "full-devops":
                    raise ValueError("Invalid tool.")
                return self.send_json(sync_stackexchange(tool, tag, max(1, min(limit, 12))))
            return self.send_error_json("API endpoint not found", 404)
        except PermissionError as exc:
            self.send_error_json(str(exc), 403)
        except (ValueError, TypeError, sqlite3.Error) as exc:
            self.send_error_json(str(exc), 400)
        except Exception as exc:
            audit("server_error", repr(exc))
            self.send_error_json("Unexpected local server error. Check the console log.", 500)


def run_server(host: str, port: int, open_browser: bool) -> None:
    init_db()
    requested_port = port
    server = None
    last_error = None
    for candidate_port in range(requested_port, requested_port + 20):
        try:
            server = ThreadingHTTPServer((host, candidate_port), AppHandler)
            port = candidate_port
            break
        except OSError as exc:
            last_error = exc
            continue
    if server is None:
        raise OSError(f"No free local port was available from {requested_port} to {requested_port + 19}") from last_error
    url = f"http://{host}:{port}"
    print("=" * 72)
    print(f"{APP_NAME} v{VERSION}")
    print(f"Dashboard: {url}")
    print("Interface: 4K Precision Dark Studio UI v2.9.0 + Adaptive AI Control Center")
    if port != requested_port:
        print(f"Notice: port {requested_port} was already in use; this build opened on port {port} instead.")
    print(f"Database:  {DB_PATH}")
    print("Press Ctrl+C to stop. Data remains on this drive.")
    print("=" * 72)
    if open_browser:
        threading.Timer(0.9, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nStopping Billinger Bot...")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--host", default="127.0.0.1", help="Bind address. Keep 127.0.0.1 for local-only operation.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--init-only", action="store_true", help="Initialize the database and exit.")
    args = parser.parse_args()
    init_db()
    if args.init_only:
        print(f"Initialized {DB_PATH}")
        return
    run_server(args.host, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
