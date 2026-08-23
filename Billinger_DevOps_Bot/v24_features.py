"""Billinger v2.4 Career & Portfolio Command Centre.

Standard-library only. Provides verified candidate profiles, explainable job matching,
approved-source job discovery, truthful resume tailoring, portfolio generation,
email drafts/Gmail OAuth sending, application tracking, company research, and
job-specific interview preparation.

Security principles:
- Localhost-only caller and student-session authorization are enforced by app.py.
- No fabricated experience: generated documents use only verified profile/project data.
- No blind auto-apply: sending requires an explicit SEND confirmation.
- No anti-bot bypass: only official/public feeds and user-approved URLs are scanned.
- Outbound HTTP is protected against SSRF and private-network access.
"""
from __future__ import annotations

import base64
import datetime as dt
import email.policy
import hashlib
import html
import io
import ipaddress
import json
import mimetypes
import os
import re
import secrets
import shutil
import socket
import sqlite3
import ssl
import struct
import subprocess
import tempfile
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from email.message import EmailMessage
from email.utils import parseaddr
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, Callable
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CAREER_DIR = Path(os.environ.get("BILLINGER_CAREER_DIR", str(BASE_DIR / "career_data"))).resolve()
PORTFOLIO_DIR = Path(os.environ.get("BILLINGER_PORTFOLIO_DIR", str(BASE_DIR / "portfolios"))).resolve()
OUTBOX_DIR = Path(os.environ.get("BILLINGER_OUTBOX_DIR", str(BASE_DIR / "mail_outbox"))).resolve()
TOKEN_DIR = Path(os.environ.get("BILLINGER_TOKEN_DIR", str(DATA_DIR / "secure_tokens"))).resolve()
DB_PATH = Path(os.environ.get("BILLINGER_DB_PATH", str(DATA_DIR / "billinger.db"))).resolve()
VERSION = "2.6.2"

MAX_JOB_DESCRIPTION = 120_000
MAX_PROFILE_TEXT = 250_000
MAX_EMAIL_ATTACHMENT = 12 * 1024 * 1024
MAX_REMOTE_BYTES = 4 * 1024 * 1024
MAX_SOURCE_JOBS = 100
ALLOWED_SOURCE_TYPES = {"greenhouse", "lever", "rss", "career_url"}
APPLICATION_STATUSES = {
    "discovered", "recommended", "resume_prepared", "awaiting_approval", "applied",
    "follow_up_due", "recruiter_replied", "assessment", "interview_scheduled",
    "rejected", "offer", "closed", "assisted_application",
}
PORTFOLIO_STATUSES = {"draft", "needs_evidence", "needs_correction", "ready_for_review", "approved", "portfolio_ready", "archived"}

SCHEMA_V24 = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS candidate_profiles (
    student_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    headline TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    skills_json TEXT NOT NULL DEFAULT '[]',
    experience_json TEXT NOT NULL DEFAULT '[]',
    education_json TEXT NOT NULL DEFAULT '[]',
    certifications_json TEXT NOT NULL DEFAULT '[]',
    projects_json TEXT NOT NULL DEFAULT '[]',
    preferences_json TEXT NOT NULL DEFAULT '{}',
    links_json TEXT NOT NULL DEFAULT '{}',
    master_resume_text TEXT NOT NULL DEFAULT '',
    verified INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS job_sources (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    name TEXT NOT NULL,
    identifier TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    last_scan_at TEXT NOT NULL DEFAULT '',
    last_result TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS job_posts (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    external_id TEXT NOT NULL DEFAULT '',
    fingerprint TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    workplace_type TEXT NOT NULL DEFAULT '',
    employment_type TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL,
    requirements_json TEXT NOT NULL DEFAULT '{}',
    match_score REAL NOT NULL DEFAULT 0,
    match_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'discovered',
    closing_date TEXT NOT NULL DEFAULT '',
    discovered_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(student_id, fingerprint),
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS portfolio_projects (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    origin TEXT NOT NULL,
    level TEXT NOT NULL,
    tools_json TEXT NOT NULL DEFAULT '[]',
    problem_statement TEXT NOT NULL DEFAULT '',
    business_requirement TEXT NOT NULL DEFAULT '',
    architecture TEXT NOT NULL DEFAULT '',
    responsibilities TEXT NOT NULL DEFAULT '',
    implementation TEXT NOT NULL DEFAULT '',
    security_controls TEXT NOT NULL DEFAULT '',
    testing TEXT NOT NULL DEFAULT '',
    monitoring TEXT NOT NULL DEFAULT '',
    troubleshooting TEXT NOT NULL DEFAULT '',
    rollback TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL DEFAULT '',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    repository_url TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    score REAL NOT NULL DEFAULT 0,
    report_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS portfolio_builds (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    template TEXT NOT NULL,
    target_job_id TEXT NOT NULL DEFAULT '',
    selected_projects_json TEXT NOT NULL DEFAULT '[]',
    folder_name TEXT NOT NULL,
    website_file TEXT NOT NULL,
    pdf_file TEXT NOT NULL,
    zip_file TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS resume_variants (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    job_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    text_file TEXT NOT NULL,
    html_file TEXT NOT NULL,
    docx_file TEXT NOT NULL,
    pdf_file TEXT NOT NULL,
    match_score REAL NOT NULL,
    included_keywords_json TEXT NOT NULL DEFAULT '[]',
    missing_keywords_json TEXT NOT NULL DEFAULT '[]',
    selected_projects_json TEXT NOT NULL DEFAULT '[]',
    change_log_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS email_drafts (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    job_id TEXT NOT NULL DEFAULT '',
    resume_variant_id TEXT NOT NULL DEFAULT '',
    portfolio_build_id TEXT NOT NULL DEFAULT '',
    recipient TEXT NOT NULL,
    cc TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    attachment_json TEXT NOT NULL DEFAULT '[]',
    eml_file TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    gmail_message_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS job_applications (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    resume_variant_id TEXT NOT NULL DEFAULT '',
    portfolio_build_id TEXT NOT NULL DEFAULT '',
    email_draft_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT '',
    follow_up_date TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS research_reports (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    source_url TEXT NOT NULL DEFAULT '',
    company_summary TEXT NOT NULL DEFAULT '',
    interview_basis TEXT NOT NULL,
    likely_rounds_json TEXT NOT NULL DEFAULT '[]',
    topics_json TEXT NOT NULL DEFAULT '[]',
    questions_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS career_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_job_posts_student_status ON job_posts(student_id,status);
CREATE INDEX IF NOT EXISTS idx_portfolio_student ON portfolio_projects(student_id,status);
CREATE INDEX IF NOT EXISTS idx_applications_student ON job_applications(student_id,status);
"""

STUDENT_SESSIONS: dict[str, tuple[int, dt.datetime]] = {}
OAUTH_STATES: dict[str, tuple[int, dt.datetime, str]] = {}
AUTH_FAILURES: dict[str, list[dt.datetime]] = {}
SEND_EVENTS: dict[int, list[dt.datetime]] = {}

SKILL_ALIASES = {
    "linux": ["linux", "ubuntu", "rhel", "centos", "systemd", "bash"],
    "networking": ["networking", "tcp/ip", "dns", "http", "https", "load balancer", "vpc"],
    "git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "shell": ["shell", "bash", "powershell", "scripting"],
    "python": ["python", "pytest", "automation scripts"],
    "docker": ["docker", "container", "dockerfile", "containerd"],
    "kubernetes": ["kubernetes", "k8s", "kubectl", "helm", "openshift", "eks", "aks", "gke"],
    "cicd": ["ci/cd", "continuous integration", "continuous delivery", "pipeline", "release automation"],
    "jenkins": ["jenkins", "jenkinsfile"],
    "github actions": ["github actions", "workflow yaml"],
    "terraform": ["terraform", "hcl", "infrastructure as code", "iac"],
    "ansible": ["ansible", "playbook", "configuration management"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "iam", "cloudwatch", "eks"],
    "azure": ["azure", "aks", "azure devops"],
    "gcp": ["gcp", "google cloud", "gke", "cloud run"],
    "prometheus": ["prometheus", "promql"],
    "grafana": ["grafana"],
    "logging": ["elk", "elasticsearch", "logstash", "kibana", "opensearch", "splunk"],
    "devsecops": ["devsecops", "sast", "dast", "sbom", "trivy", "sonarqube", "supply chain"],
    "sre": ["sre", "site reliability", "slo", "sli", "error budget", "incident response"],
    "databases": ["postgresql", "mysql", "sql", "database", "redis"],
}

STOPWORDS = {
    "the","and","for","with","that","this","from","your","you","are","will","have","has","our","their","into",
    "using","use","used","job","role","work","team","experience","skills","required","preferred","ability","strong",
    "years","year","candidate","responsible","responsibilities","including","knowledge","support","company","about",
}

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("generic secret assignment", re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\"]{8,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
]


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
    return None if row is None else {key: row[key] for key in row.keys()}


def _clean(value: Any, limit: int = 100_000) -> str:
    return str(value or "").replace("\x00", "").strip()[:limit]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _stored_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(BASE_DIR.resolve()))
    except ValueError:
        return str(resolved)


def _resolved_stored_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (BASE_DIR / path).resolve()


def _load_json(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return default


def _student_exists(student_id: int) -> bool:
    with _connect() as conn:
        return bool(conn.execute("SELECT 1 FROM students WHERE id=?", (student_id,)).fetchone())


def _audit(student_id: int | None, action: str, detail: str) -> None:
    with _connect() as conn:
        conn.execute("INSERT INTO career_audit(student_id,action,detail,created_at) VALUES(?,?,?,?)", (student_id, _clean(action, 80), _clean(detail, 2000), now_iso()))


def init_v24_db() -> None:
    for folder in (CAREER_DIR, PORTFOLIO_DIR, OUTBOX_DIR, TOKEN_DIR):
        folder.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(SCHEMA_V24)
        conn.commit()


def create_student_session(student_id: int, pin: str, verify_pin_fn: Callable[[str, str], bool]) -> dict[str, Any]:
    key = f"student:{student_id}"
    now = dt.datetime.now(dt.timezone.utc)
    recent = [x for x in AUTH_FAILURES.get(key, []) if (now - x).total_seconds() < 900]
    AUTH_FAILURES[key] = recent
    if len(recent) >= 8:
        raise PermissionError("Too many failed attempts. Wait 15 minutes before trying again.")
    with _connect() as conn:
        row = conn.execute("SELECT id,name,email,pin_hash FROM students WHERE id=?", (student_id,)).fetchone()
    if not row or not verify_pin_fn(_clean(pin, 30), row["pin_hash"]):
        AUTH_FAILURES[key].append(now)
        raise PermissionError("Invalid student or PIN.")
    AUTH_FAILURES.pop(key, None)
    token = secrets.token_urlsafe(32)
    expiry = now + dt.timedelta(hours=8)
    STUDENT_SESSIONS[token] = (student_id, expiry)
    return {"authenticated": True, "token": token, "expires_at": expiry.isoformat(), "student": {"id": row["id"], "name": row["name"], "email": row["email"]}}


def require_student(token: str, student_id: int) -> None:
    value = STUDENT_SESSIONS.get(token)
    now = dt.datetime.now(dt.timezone.utc)
    if not value or value[0] != student_id or value[1] < now:
        STUDENT_SESSIONS.pop(token, None)
        raise PermissionError("Student session is missing, expired, or belongs to another profile.")


def _validate_email(address: str) -> str:
    address = _clean(address, 254)
    if any(ch in address for ch in "\r\n"):
        raise ValueError("Email headers may not contain line breaks.")
    name, parsed = parseaddr(address)
    if parsed != address or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", parsed):
        raise ValueError("Enter a valid email address.")
    return parsed


def _list_strings(value: Any, max_items: int = 200, max_len: int = 300) -> list[str]:
    if isinstance(value, str):
        items = re.split(r"[,\n;]+", value)
    elif isinstance(value, list):
        items = value
    else:
        items = []
    out: list[str] = []
    for item in items[:max_items]:
        text = _clean(item, max_len)
        if text and text.lower() not in {x.lower() for x in out}:
            out.append(text)
    return out


def _normalise_records(value: Any, max_items: int = 50) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    records: list[dict[str, str]] = []
    for raw in value[:max_items]:
        if not isinstance(raw, dict):
            continue
        records.append({str(k)[:50]: _clean(v, 5000) for k, v in raw.items() if isinstance(k, str)})
    return records


def save_candidate_profile(student_id: int, data: dict[str, Any]) -> dict[str, Any]:
    if not _student_exists(student_id):
        raise ValueError("Student was not found.")
    full_name = _clean(data.get("full_name"), 160)
    email_address = _clean(data.get("email"), 254)
    if email_address:
        email_address = _validate_email(email_address)
    skills = _list_strings(data.get("skills"), 250, 120)
    experience = _normalise_records(data.get("experience"))
    education = _normalise_records(data.get("education"))
    certifications = _normalise_records(data.get("certifications"))
    projects = _normalise_records(data.get("projects"))
    preferences = data.get("preferences") if isinstance(data.get("preferences"), dict) else {}
    links = data.get("links") if isinstance(data.get("links"), dict) else {}
    safe_links = {k: _validate_optional_public_url(v) for k, v in links.items() if k in {"github", "linkedin", "portfolio", "website"} and _clean(v, 500)}
    values = (
        full_name, email_address, _clean(data.get("phone"), 80), _clean(data.get("location"), 160),
        _clean(data.get("headline"), 240), _clean(data.get("summary"), 12_000), _json(skills), _json(experience),
        _json(education), _json(certifications), _json(projects), _json(preferences), _json(safe_links),
        _clean(data.get("master_resume_text"), MAX_PROFILE_TEXT), 1 if data.get("verified") else 0, now_iso(), student_id,
    )
    with _connect() as conn:
        conn.execute(
            """INSERT INTO candidate_profiles(student_id,full_name,email,phone,location,headline,summary,skills_json,experience_json,education_json,certifications_json,projects_json,preferences_json,links_json,master_resume_text,verified,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(student_id) DO UPDATE SET full_name=excluded.full_name,email=excluded.email,phone=excluded.phone,location=excluded.location,
            headline=excluded.headline,summary=excluded.summary,skills_json=excluded.skills_json,experience_json=excluded.experience_json,
            education_json=excluded.education_json,certifications_json=excluded.certifications_json,projects_json=excluded.projects_json,
            preferences_json=excluded.preferences_json,links_json=excluded.links_json,master_resume_text=excluded.master_resume_text,
            verified=excluded.verified,updated_at=excluded.updated_at""",
            (student_id,) + values[:-1],
        )
        conn.commit()
    _audit(student_id, "candidate_profile_saved", f"skills={len(skills)};verified={bool(data.get('verified'))}")
    return get_candidate_profile(student_id)


def get_candidate_profile(student_id: int) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM candidate_profiles WHERE student_id=?", (student_id,)).fetchone()
        student = conn.execute("SELECT name,email FROM students WHERE id=?", (student_id,)).fetchone()
    if not student:
        raise ValueError("Student was not found.")
    if not row:
        return {
            "student_id": student_id, "full_name": student["name"], "email": student["email"], "phone": "", "location": "",
            "headline": "", "summary": "", "skills": [], "experience": [], "education": [], "certifications": [],
            "projects": [], "preferences": {}, "links": {}, "master_resume_text": "", "verified": False,
        }
    data = _row(row) or {}
    for source, target, default in (
        ("skills_json", "skills", []), ("experience_json", "experience", []), ("education_json", "education", []),
        ("certifications_json", "certifications", []), ("projects_json", "projects", []),
        ("preferences_json", "preferences", {}), ("links_json", "links", {}),
    ):
        data[target] = _load_json(data.pop(source), default)
    data["verified"] = bool(data["verified"])
    return data


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _extract_terms(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(re.search(r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])", lower) for alias in aliases):
            found.append(canonical)
    words = re.findall(r"[a-z][a-z0-9+.#/-]{2,}", lower)
    common = [word for word, count in Counter(w for w in words if w not in STOPWORDS).most_common(40) if count >= 2]
    return list(dict.fromkeys(found + common))[:60]


def _years_from_profile(profile: dict[str, Any]) -> float:
    total = 0.0
    for item in profile.get("experience", []):
        try:
            total += float(item.get("years", 0) or 0)
        except (TypeError, ValueError):
            pass
    return round(total, 1)


def _match_job(profile: dict[str, Any], title: str, description: str, location: str = "") -> dict[str, Any]:
    terms = _extract_terms(description)
    profile_blob = " ".join(
        profile.get("skills", []) + [profile.get("summary", ""), profile.get("headline", ""), profile.get("master_resume_text", "")]
        + [" ".join(item.values()) for item in profile.get("experience", []) if isinstance(item, dict)]
        + [" ".join(item.values()) for item in profile.get("projects", []) if isinstance(item, dict)]
    ).lower()
    matched = [term for term in terms if term.lower() in profile_blob or any(alias in profile_blob for alias in SKILL_ALIASES.get(term, []))]
    missing = [term for term in terms if term not in matched]
    technical = [t for t in terms if t in SKILL_ALIASES]
    technical_match = len([t for t in technical if t in matched]) / max(1, len(technical))
    all_match = len(matched) / max(1, len(terms))
    title_tokens = set(re.findall(r"[a-z]{3,}", title.lower())) - STOPWORDS
    target_roles = _list_strings(profile.get("preferences", {}).get("target_roles", []), 20, 120)
    role_blob = " ".join(target_roles + [profile.get("headline", "")]).lower()
    role_match = sum(1 for token in title_tokens if token in role_blob) / max(1, len(title_tokens))
    location_pref = " ".join(_list_strings(profile.get("preferences", {}).get("locations", []), 30, 120)).lower()
    location_match = 1.0 if not location_pref or not location else (1.0 if any(x.strip() and x.strip() in location.lower() for x in location_pref.split(",")) else 0.4)
    experience_years = _years_from_profile(profile)
    requested_years = 0
    year_hits = [int(x) for x in re.findall(r"(?:minimum|min\.?|at least)?\s*(\d{1,2})\+?\s+years?", description.lower())]
    if year_hits:
        requested_years = max(year_hits)
    experience_match = 1.0 if not requested_years else min(1.0, experience_years / requested_years)
    score = round(technical_match * 40 + all_match * 20 + role_match * 15 + experience_match * 15 + location_match * 10)
    score = max(0, min(100, score))
    recommendation = "Excellent match" if score >= 90 else "Recommended" if score >= 75 else "Review manually" if score >= 60 else "Do not auto-recommend"
    return {
        "score": score, "recommendation": recommendation, "matched": matched[:30], "missing": missing[:30],
        "required_skills": technical, "experience_years": experience_years, "requested_years": requested_years,
        "components": {"technical": round(technical_match*100), "overall_keywords": round(all_match*100), "role": round(role_match*100), "experience": round(experience_match*100), "location": round(location_match*100)},
        "truth_notice": "Missing requirements are not added to the resume unless supported by verified profile or portfolio evidence.",
    }


def analyze_manual_job(student_id: int, data: dict[str, Any]) -> dict[str, Any]:
    profile = get_candidate_profile(student_id)
    title = _clean(data.get("title"), 240)
    company = _clean(data.get("company"), 240)
    description = _clean(data.get("description"), MAX_JOB_DESCRIPTION)
    if len(title) < 2 or len(company) < 2 or len(description) < 80:
        raise ValueError("Company, job title, and a fuller job description are required.")
    url = _validate_optional_public_url(data.get("url"))
    external_id = _clean(data.get("external_id"), 200)
    fingerprint = hashlib.sha256(f"{company.lower()}|{title.lower()}|{url.lower()}|{external_id.lower()}".encode()).hexdigest()
    match = _match_job(profile, title, description, _clean(data.get("location"), 200))
    job_id = "job_" + secrets.token_hex(8)
    status = "recommended" if match["score"] >= int(profile.get("preferences", {}).get("minimum_match", 75) or 75) else "discovered"
    values = (
        job_id, student_id, _clean(data.get("source_id"), 100), external_id, fingerprint, company, title,
        _clean(data.get("location"), 200), _clean(data.get("workplace_type"), 80), _clean(data.get("employment_type"), 80),
        url, description, _json({"terms": _extract_terms(description)}), match["score"], _json(match), status,
        _clean(data.get("closing_date"), 30), now_iso(), now_iso(),
    )
    with _connect() as conn:
        existing = conn.execute("SELECT id FROM job_posts WHERE student_id=? AND fingerprint=?", (student_id, fingerprint)).fetchone()
        if existing:
            job_id = existing["id"]
            conn.execute("UPDATE job_posts SET description=?,match_score=?,match_json=?,updated_at=? WHERE id=?", (description, match["score"], _json(match), now_iso(), job_id))
        else:
            conn.execute("INSERT INTO job_posts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        conn.commit()
    _audit(student_id, "job_analyzed", f"{company} | {title} | score={match['score']}")
    return get_job(student_id, job_id)


def list_jobs(student_id: int, status: str = "") -> list[dict[str, Any]]:
    sql = "SELECT * FROM job_posts WHERE student_id=?"
    params: list[Any] = [student_id]
    if status:
        sql += " AND status=?"; params.append(status)
    sql += " ORDER BY match_score DESC,discovered_at DESC LIMIT 500"
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_public_job(_row(row) or {}) for row in rows]


def get_job(student_id: int, job_id: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM job_posts WHERE id=? AND student_id=?", (_clean(job_id, 100), student_id)).fetchone()
    if not row:
        raise ValueError("Job was not found for this student.")
    return _public_job(_row(row) or {})


def _public_job(data: dict[str, Any]) -> dict[str, Any]:
    data["requirements"] = _load_json(data.pop("requirements_json", "{}"), {})
    data["match"] = _load_json(data.pop("match_json", "{}"), {})
    return data


def save_job_status(student_id: int, job_id: str, status: str) -> dict[str, Any]:
    status = _clean(status, 40)
    if status not in APPLICATION_STATUSES:
        raise ValueError("Invalid job/application status.")
    with _connect() as conn:
        cur = conn.execute("UPDATE job_posts SET status=?,updated_at=? WHERE id=? AND student_id=?", (status, now_iso(), job_id, student_id))
        if not cur.rowcount:
            raise ValueError("Job was not found.")
        conn.commit()
    return get_job(student_id, job_id)


def add_job_source(student_id: int, source_type: str, name: str, identifier: str) -> dict[str, Any]:
    source_type = _clean(source_type, 30).lower()
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError("Source type must be Greenhouse, Lever, RSS, or a public careers page.")
    identifier = _clean(identifier, 1000)
    if source_type in {"rss", "career_url"}:
        identifier = _validate_public_url(identifier)
    elif not re.fullmatch(r"[A-Za-z0-9._-]{2,120}", identifier):
        raise ValueError("ATS board identifier contains unsupported characters.")
    source_id = "src_" + secrets.token_hex(7)
    with _connect() as conn:
        conn.execute("INSERT INTO job_sources(id,student_id,source_type,name,identifier,created_at) VALUES(?,?,?,?,?,?)", (source_id, student_id, source_type, _clean(name, 160) or identifier, identifier, now_iso()))
        conn.commit()
    return {"id": source_id, "source_type": source_type, "name": name or identifier, "identifier": identifier, "active": True}


def list_job_sources(student_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        return [_row(r) or {} for r in conn.execute("SELECT * FROM job_sources WHERE student_id=? ORDER BY created_at DESC", (student_id,)).fetchall()]


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = ""
        self._text: list[str] = []
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href") or ""; self._text = []
    def handle_data(self, data: str) -> None:
        if self._href: self._text.append(data)
    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = ""; self._text = []


def _validate_optional_public_url(value: Any) -> str:
    value = _clean(value, 1000)
    return _validate_public_url(value) if value else ""


def _validate_public_url(url: str) -> str:
    parsed = urllib.parse.urlparse(_clean(url, 1000))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTPS URLs without embedded credentials are allowed.")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise ValueError("Localhost and private-network URLs are blocked.")
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("The public hostname could not be resolved.") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise ValueError("Private, loopback, link-local, and reserved network addresses are blocked.")
    return urllib.parse.urlunparse(("https", parsed.netloc, parsed.path or "/", parsed.params, parsed.query, ""))


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe = _validate_public_url(urllib.parse.urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, safe)


def safe_fetch(url: str, accept: str = "application/json,text/html,application/rss+xml", max_bytes: int = MAX_REMOTE_BYTES) -> tuple[bytes, str, str]:
    url = _validate_public_url(url)
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    request = urllib.request.Request(url, headers={"User-Agent": f"BillingerBot/{VERSION} job-discovery; local-user-request", "Accept": accept})
    try:
        with opener.open(request, timeout=20, context=ssl.create_default_context()) as response:  # type: ignore[arg-type]
            content_type = response.headers.get_content_type()
            final_url = _validate_public_url(response.geturl())
            length = response.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                raise ValueError("Remote response exceeds the allowed size.")
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("Remote response exceeds the allowed size.")
            return raw, content_type, final_url
    except TypeError:
        # Python opener.open does not accept context; HTTPSHandler already uses verified SSL.
        try:
            with opener.open(request, timeout=20) as response:
                content_type = response.headers.get_content_type()
                final_url = _validate_public_url(response.geturl())
                raw = response.read(max_bytes + 1)
                if len(raw) > max_bytes: raise ValueError("Remote response exceeds the allowed size.")
                return raw, content_type, final_url
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ValueError(f"Public source request failed: {exc}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError(f"Public source request failed: {exc}") from exc


def _robots_allows(url: str, fetcher: Callable[..., tuple[bytes, str, str]]) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = urllib.parse.urlunparse(("https", parsed.netloc, "/robots.txt", "", "", ""))
    try:
        raw, _, _ = fetcher(robots_url, "text/plain", 512_000)
    except Exception:
        return True
    text = raw.decode("utf-8", errors="ignore")
    current_all = False
    disallows: list[str] = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line: continue
        key, _, value = line.partition(":")
        key = key.strip().lower(); value = value.strip()
        if key == "user-agent": current_all = value == "*"
        elif key == "disallow" and current_all and value: disallows.append(value)
    path = parsed.path or "/"
    return not any(path.startswith(rule) for rule in disallows)


def _job_from_greenhouse(item: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    content = _strip_html(item.get("content", ""))
    offices = item.get("offices") or []
    location = (item.get("location") or {}).get("name", "") or ", ".join(x.get("name", "") for x in offices if isinstance(x, dict))
    return {"source_id": source["id"], "external_id": str(item.get("id", "")), "company": source["name"], "title": item.get("title", ""), "location": location, "url": item.get("absolute_url", ""), "description": content or item.get("title", "")}


def _job_from_lever(item: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    categories = item.get("categories") or {}
    description = "\n".join([item.get("descriptionPlain", ""), item.get("additionalPlain", ""), "\n".join(x.get("content", "") for x in item.get("lists", []) if isinstance(x, dict))])
    return {"source_id": source["id"], "external_id": str(item.get("id", "")), "company": source["name"], "title": item.get("text", ""), "location": categories.get("location", ""), "employment_type": categories.get("commitment", ""), "url": item.get("hostedUrl", ""), "description": description}


def scan_job_sources(student_id: int, source_id: str = "", fetcher: Callable[..., tuple[bytes, str, str]] = safe_fetch) -> dict[str, Any]:
    sources = [x for x in list_job_sources(student_id) if x.get("active")]
    if source_id:
        sources = [x for x in sources if x["id"] == source_id]
    imported = 0; duplicates = 0; errors: list[str] = []
    for source in sources:
        jobs: list[dict[str, Any]] = []
        try:
            stype = source["source_type"]; ident = source["identifier"]
            if stype == "greenhouse":
                url = f"https://boards-api.greenhouse.io/v1/boards/{urllib.parse.quote(ident)}/jobs?content=true"
                raw, _, _ = fetcher(url, "application/json", MAX_REMOTE_BYTES)
                payload = json.loads(raw.decode("utf-8")); jobs = [_job_from_greenhouse(x, source) for x in payload.get("jobs", [])[:MAX_SOURCE_JOBS]]
            elif stype == "lever":
                url = f"https://api.lever.co/v0/postings/{urllib.parse.quote(ident)}?mode=json"
                raw, _, _ = fetcher(url, "application/json", MAX_REMOTE_BYTES)
                payload = json.loads(raw.decode("utf-8")); jobs = [_job_from_lever(x, source) for x in payload[:MAX_SOURCE_JOBS]]
            elif stype == "rss":
                raw, _, final = fetcher(ident, "application/rss+xml,application/xml,text/xml", MAX_REMOTE_BYTES)
                root = ET.fromstring(raw)
                for item in root.findall(".//item")[:MAX_SOURCE_JOBS]:
                    title = "".join(item.findtext("title") or "")
                    link = item.findtext("link") or ""
                    desc = _strip_html(item.findtext("description") or "")
                    jobs.append({"source_id": source["id"], "external_id": link, "company": source["name"], "title": title, "url": urllib.parse.urljoin(final, link), "description": desc or title})
            elif stype == "career_url":
                if not _robots_allows(ident, fetcher):
                    raise ValueError("robots.txt does not permit automated access to this careers URL.")
                raw, _, final = fetcher(ident, "text/html", MAX_REMOTE_BYTES)
                parser = _LinkParser(); parser.feed(raw.decode("utf-8", errors="ignore"))
                seen: set[str] = set()
                for href, label in parser.links:
                    absolute = urllib.parse.urljoin(final, href)
                    if not re.search(r"(?i)(job|career|position|vacan|opening|apply)", absolute + " " + label): continue
                    try: absolute = _validate_public_url(absolute)
                    except ValueError: continue
                    if absolute in seen: continue
                    seen.add(absolute)
                    title = label.strip() or urllib.parse.unquote(Path(urllib.parse.urlparse(absolute).path).name).replace("-", " ")
                    jobs.append({"source_id": source["id"], "external_id": absolute, "company": source["name"], "title": title[:240], "url": absolute, "description": f"Public careers-page listing: {title}. Open the official page and paste the complete description for a precise match."})
                    if len(jobs) >= 30: break
            for job in jobs:
                try:
                    before = len(list_jobs(student_id))
                    analyze_manual_job(student_id, job)
                    after = len(list_jobs(student_id))
                    if after > before: imported += 1
                    else: duplicates += 1
                except ValueError as exc:
                    errors.append(f"{source['name']}: {exc}")
            with _connect() as conn:
                conn.execute("UPDATE job_sources SET last_scan_at=?,last_result=? WHERE id=?", (now_iso(), f"jobs={len(jobs)};imported={imported};duplicates={duplicates}", source["id"]))
                conn.commit()
        except Exception as exc:
            errors.append(f"{source['name']}: {exc}")
    _audit(student_id, "job_sources_scanned", f"sources={len(sources)};imported={imported};errors={len(errors)}")
    return {"sources_scanned": len(sources), "imported": imported, "duplicates": duplicates, "errors": errors[:20], "jobs": list_jobs(student_id)}


def scan_secrets(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for name, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({"type": name, "preview": match.group(0)[:4] + "…REDACTED", "position": str(match.start())})
    return findings[:50]


def save_portfolio_project(student_id: int, data: dict[str, Any]) -> dict[str, Any]:
    project_id = _clean(data.get("id"), 100) or "proj_" + secrets.token_hex(8)
    title = _clean(data.get("title"), 240)
    if len(title) < 3:
        raise ValueError("Project title is required.")
    origin = _clean(data.get("origin"), 80) or "Independent project"
    if origin not in {"Independent project", "Guided course project", "Simulated company assignment", "Practical assessment", "Professional work experience"}:
        raise ValueError("Invalid portfolio project origin.")
    tools = _list_strings(data.get("tools"), 60, 80)
    fields = {key: _clean(data.get(key), 30_000) for key in (
        "problem_statement","business_requirement","architecture","responsibilities","implementation","security_controls",
        "testing","monitoring","troubleshooting","rollback","outcome",
    )}
    evidence = _list_strings(data.get("evidence"), 100, 500)
    combined = "\n".join(fields.values()) + "\n" + "\n".join(evidence)
    secrets_found = scan_secrets(combined)
    dimensions = {
        "technical_correctness": min(100, 25 + len(tools)*7 + len(fields["implementation"])//80),
        "documentation": min(100, sum(bool(fields[x]) for x in fields)*9),
        "evidence": min(100, len(evidence)*20),
        "security": 100 if fields["security_controls"] and not secrets_found else 20 if secrets_found else 40,
        "observability": 100 if fields["monitoring"] else 30,
        "rollback": 100 if fields["rollback"] else 25,
        "business": 100 if fields["business_requirement"] and fields["outcome"] else 45,
        "presentation": 90 if len(title) >= 8 and fields["architecture"] else 60,
    }
    weights = {"technical_correctness":.25,"documentation":.15,"evidence":.15,"security":.10,"observability":.10,"rollback":.10,"business":.10,"presentation":.05}
    score = round(sum(dimensions[k]*weights[k] for k in weights), 1)
    requested_status = _clean(data.get("status"), 40) or "draft"
    if secrets_found: status = "needs_correction"
    elif score >= 75 and evidence: status = "portfolio_ready" if requested_status in {"approved","portfolio_ready"} else "ready_for_review"
    elif not evidence: status = "needs_evidence"
    else: status = "needs_correction"
    report = {"dimensions": dimensions, "secret_findings": secrets_found, "score": score, "status": status, "notice": "Training projects are labelled by origin and are never presented as employment unless explicitly verified as professional work."}
    with _connect() as conn:
        exists = conn.execute("SELECT 1 FROM portfolio_projects WHERE id=? AND student_id=?", (project_id, student_id)).fetchone()
        values = (
            title, origin, _clean(data.get("level"), 30) or "Beginner", _json(tools), fields["problem_statement"], fields["business_requirement"],
            fields["architecture"], fields["responsibilities"], fields["implementation"], fields["security_controls"], fields["testing"], fields["monitoring"],
            fields["troubleshooting"], fields["rollback"], fields["outcome"], _json(evidence), _validate_optional_public_url(data.get("repository_url")),
            status, score, _json(report), now_iso(),
        )
        if exists:
            conn.execute("""UPDATE portfolio_projects SET title=?,origin=?,level=?,tools_json=?,problem_statement=?,business_requirement=?,architecture=?,responsibilities=?,implementation=?,security_controls=?,testing=?,monitoring=?,troubleshooting=?,rollback=?,outcome=?,evidence_json=?,repository_url=?,status=?,score=?,report_json=?,updated_at=? WHERE id=? AND student_id=?""", values + (project_id, student_id))
        else:
            conn.execute("""INSERT INTO portfolio_projects(id,student_id,title,origin,level,tools_json,problem_statement,business_requirement,architecture,responsibilities,implementation,security_controls,testing,monitoring,troubleshooting,rollback,outcome,evidence_json,repository_url,status,score,report_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (project_id, student_id) + values[:-1] + (values[-1], values[-1]))
        conn.commit()
    _audit(student_id, "portfolio_project_saved", f"{title};score={score};status={status}")
    return get_portfolio_project(student_id, project_id)


def _public_project(data: dict[str, Any]) -> dict[str, Any]:
    data["tools"] = _load_json(data.pop("tools_json", "[]"), [])
    data["evidence"] = _load_json(data.pop("evidence_json", "[]"), [])
    data["report"] = _load_json(data.pop("report_json", "{}"), {})
    return data


def get_portfolio_project(student_id: int, project_id: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM portfolio_projects WHERE id=? AND student_id=?", (project_id, student_id)).fetchone()
    if not row: raise ValueError("Portfolio project was not found.")
    return _public_project(_row(row) or {})


def list_portfolio_projects(student_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM portfolio_projects WHERE student_id=? ORDER BY score DESC,updated_at DESC", (student_id,)).fetchall()
    return [_public_project(_row(r) or {}) for r in rows]


def _xml_escape(text: str) -> str:
    return html.escape(text, quote=False)


def make_docx(paragraphs: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    body = "".join(f'<w:p><w:r><w:t xml:space="preserve">{_xml_escape(p)}</w:t></w:r></w:p>' for p in paragraphs)
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="900" w:right="900" w:bottom="900" w:left="900"/></w:sectPr></w:body></w:document>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types); zf.writestr("_rels/.rels", rels); zf.writestr("word/document.xml", document)


def make_simple_pdf(lines: list[str], path: Path, title: str = "Billinger Document") -> None:
    """Create a small, text-only PDF without third-party packages."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=92) or [""])
    pages = [wrapped[i:i+48] for i in range(0, len(wrapped), 48)] or [[title]]
    objects: list[bytes] = []
    def add(obj: str | bytes) -> int:
        objects.append(obj.encode("latin-1", errors="replace") if isinstance(obj, str) else obj); return len(objects)
    catalog_id = add("")
    pages_id = add("")
    font_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []
    for page_lines in pages:
        commands = ["BT", "/F1 10 Tf", "50 790 Td", "13 TL"]
        for line in page_lines:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({safe}) Tj"); commands.append("T*")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        content_id = add(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        page_id = add(f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>")
        page_ids.append(page_id)
    objects[catalog_id-1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
    objects[pages_id-1] = f"<< /Type /Pages /Kids [{' '.join(f'{x} 0 R' for x in page_ids)}] /Count {len(page_ids)} >>".encode()
    out = io.BytesIO(); out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(out.tell()); out.write(f"{i} 0 obj\n".encode()); out.write(obj); out.write(b"\nendobj\n")
    xref = out.tell(); out.write(f"xref\n0 {len(objects)+1}\n".encode()); out.write(b"0000000000 65535 f \n")
    for off in offsets[1:]: out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects)+1} /Root {catalog_id} 0 R /Info << /Title ({title.replace('(','').replace(')','')}) >> >>\nstartxref\n{xref}\n%%EOF".encode("latin-1", errors="replace"))
    path.write_bytes(out.getvalue())


def _project_relevance(project: dict[str, Any], terms: list[str]) -> int:
    blob = (project["title"] + " " + " ".join(project.get("tools", [])) + " " + project.get("implementation", "") + " " + project.get("outcome", "")).lower()
    return sum(1 for term in terms if term.lower() in blob)


def generate_portfolio(student_id: int, data: dict[str, Any]) -> dict[str, Any]:
    profile = get_candidate_profile(student_id)
    projects = list_portfolio_projects(student_id)
    job_id = _clean(data.get("job_id"), 100)
    job = get_job(student_id, job_id) if job_id else None
    terms = (job or {}).get("match", {}).get("required_skills", []) or _list_strings(data.get("focus_skills"), 30, 80)
    requested = _list_strings(data.get("project_ids"), 30, 100)
    eligible = [p for p in projects if p["status"] in {"approved", "portfolio_ready", "ready_for_review"} and not p.get("report", {}).get("secret_findings")]
    if requested: eligible = [p for p in eligible if p["id"] in requested]
    eligible.sort(key=lambda p: (_project_relevance(p, terms), p["score"]), reverse=True)
    selected = eligible[:8]
    if not selected:
        raise ValueError("No portfolio-ready projects are available. Add evidence and pass project review first.")
    build_id = "portfolio_" + secrets.token_hex(7)
    folder = PORTFOLIO_DIR / f"student_{student_id}" / build_id
    folder.mkdir(parents=True, exist_ok=True)
    template = _clean(data.get("template"), 60) or "DevOps Command Centre"
    name = profile.get("full_name") or f"Student {student_id}"
    headline = profile.get("headline") or "DevOps Portfolio"
    cards = []
    for p in selected:
        cards.append(f"<article class='project'><span>{html.escape(p['origin'])} · {html.escape(p['level'])}</span><h2>{html.escape(p['title'])}</h2><p>{html.escape(p['problem_statement'] or p['business_requirement'])}</p><div class='tags'>{''.join(f'<b>{html.escape(x)}</b>' for x in p['tools'])}</div><h3>Implementation</h3><p>{html.escape(p['implementation'])}</p><h3>Validation and outcome</h3><p>{html.escape(p['testing'])}</p><p>{html.escape(p['outcome'])}</p><small>Portfolio score: {p['score']}% · {html.escape(p['status'])}</small></article>")
    css = """*{box-sizing:border-box}body{margin:0;background:#06101d;color:#dbeafe;font:16px/1.6 system-ui;padding:48px;background-image:radial-gradient(circle at 20% 10%,#0c4a6e55,transparent 30%),linear-gradient(#06101d,#030712)}main{max-width:1100px;margin:auto}.hero{padding:56px;border:1px solid #22d3ee55;background:#0f172acc;border-radius:28px;box-shadow:0 30px 80px #0008}.hero h1{font-size:48px;margin:0;color:#67e8f9}.skills,.tags{display:flex;gap:8px;flex-wrap:wrap}.skills b,.tags b{padding:6px 10px;border:1px solid #38bdf866;border-radius:999px;background:#082f49}.project{margin-top:24px;padding:28px;border:1px solid #818cf855;background:#111827cc;border-radius:22px;box-shadow:0 20px 50px #0005}.project span{color:#a5b4fc}.project h2{color:#e0f2fe}a{color:#67e8f9}@media(max-width:700px){body{padding:16px}.hero{padding:28px}.hero h1{font-size:34px}}"""
    links = profile.get("links", {})
    site = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>{html.escape(name)} — DevOps Portfolio</title><style>{css}</style></head><body><main><section class='hero'><small>VERIFIED DEVOPS PORTFOLIO · {html.escape(template)}</small><h1>{html.escape(name)}</h1><h2>{html.escape(headline)}</h2><p>{html.escape(profile.get('summary',''))}</p><div class='skills'>{''.join(f'<b>{html.escape(x)}</b>' for x in profile.get('skills',[]))}</div><p>{' · '.join(f"<a href='{html.escape(v)}'>{html.escape(k.title())}</a>" for k,v in links.items() if v)}</p><p>Projects are labelled by origin. Simulated or guided work is not represented as employment.</p></section>{''.join(cards)}</main></body></html>"""
    index_file = folder / "index.html"; index_file.write_text(site, encoding="utf-8")
    lines = [name, headline, profile.get("summary", ""), "Skills: " + ", ".join(profile.get("skills", [])), ""]
    for p in selected:
        lines.extend([p["title"], f"Origin: {p['origin']} | Level: {p['level']} | Score: {p['score']}%", "Tools: " + ", ".join(p["tools"]), p["problem_statement"], p["implementation"], "Validation: " + p["testing"], "Outcome: " + p["outcome"], ""])
    pdf_file = folder / "portfolio_summary.pdf"; make_simple_pdf(lines, pdf_file, f"{name} DevOps Portfolio")
    zip_file = folder.with_suffix(".zip")
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(index_file, "index.html"); zf.write(pdf_file, "portfolio_summary.pdf")
        for p in selected:
            readme = f"# {p['title']}\n\n**Origin:** {p['origin']}\n\n## Problem\n{p['problem_statement']}\n\n## Architecture\n{p['architecture']}\n\n## Implementation\n{p['implementation']}\n\n## Security\n{p['security_controls']}\n\n## Testing\n{p['testing']}\n\n## Rollback\n{p['rollback']}\n\n## Outcome\n{p['outcome']}\n"
            zf.writestr(f"projects/{re.sub(r'[^a-z0-9]+','-',p['title'].lower()).strip('-')}/README.md", readme)
    with _connect() as conn:
        conn.execute("INSERT INTO portfolio_builds VALUES(?,?,?,?,?,?,?,?,?,?,?)", (build_id, student_id, f"{name} DevOps Portfolio", template, job_id, _json([p["id"] for p in selected]), folder.name, _stored_path(index_file), _stored_path(pdf_file), _stored_path(zip_file), now_iso()))
        conn.commit()
    _audit(student_id, "portfolio_generated", f"build={build_id};projects={len(selected)};job={job_id or 'general'}")
    return get_portfolio_build(student_id, build_id)


def get_portfolio_build(student_id: int, build_id: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM portfolio_builds WHERE id=? AND student_id=?", (build_id, student_id)).fetchone()
    if not row: raise ValueError("Portfolio build was not found.")
    data = _row(row) or {}; data["selected_projects"] = _load_json(data.pop("selected_projects_json", "[]"), [])
    data["links"] = {"website": f"/api/v4/portfolio/file?id={build_id}&format=html", "pdf": f"/api/v4/portfolio/file?id={build_id}&format=pdf", "zip": f"/api/v4/portfolio/file?id={build_id}&format=zip"}
    return data


def list_portfolio_builds(student_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM portfolio_builds WHERE student_id=? ORDER BY created_at DESC", (student_id,)).fetchall()]
    return [get_portfolio_build(student_id, x) for x in ids]


def portfolio_file(student_id: int, build_id: str, fmt: str) -> tuple[Path, str, str, bool]:
    build = get_portfolio_build(student_id, build_id)
    if fmt == "html": rel, mime, inline = build["website_file"], "text/html; charset=utf-8", True
    elif fmt == "pdf": rel, mime, inline = build["pdf_file"], "application/pdf", True
    else: rel, mime, inline = build["zip_file"], "application/zip", False
    path = _resolved_stored_path(rel)
    roots = [PORTFOLIO_DIR.resolve()]
    if not any(root == path or root in path.parents for root in roots) or not path.is_file(): raise ValueError("Portfolio file is unavailable.")
    return path, mime, path.name, inline


def _resume_content(profile: dict[str, Any], job: dict[str, Any] | None, projects: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str], list[str]]:
    required = (job or {}).get("match", {}).get("required_skills", [])
    profile_blob = (" ".join(profile.get("skills", [])) + " " + profile.get("master_resume_text", "")).lower()
    included = [x for x in required if x in profile_blob or any(alias in profile_blob for alias in SKILL_ALIASES.get(x, []))]
    missing = [x for x in required if x not in included]
    skills = sorted(profile.get("skills", []), key=lambda x: (0 if x.lower() in included else 1, x.lower()))
    lines = [profile.get("full_name", ""), profile.get("headline", "DevOps Professional"), " | ".join(x for x in [profile.get("email",""), profile.get("phone",""), profile.get("location","")] if x)]
    links = profile.get("links", {}); link_line = " | ".join(f"{k.title()}: {v}" for k,v in links.items() if v)
    if link_line: lines.append(link_line)
    lines.extend(["", "PROFESSIONAL SUMMARY", profile.get("summary", ""), "", "TECHNICAL SKILLS", ", ".join(skills)])
    if profile.get("experience"):
        lines.extend(["", "EXPERIENCE"])
        for item in profile["experience"]:
            heading = " — ".join(x for x in [item.get("role",""), item.get("company","")] if x); lines.append(heading)
            details = item.get("details") or item.get("responsibilities") or ""; lines.append(details)
    if projects:
        lines.extend(["", "SELECTED DEVOPS PORTFOLIO PROJECTS"])
        for p in projects:
            lines.append(p["title"]); lines.append(f"{p['origin']} | Tools: {', '.join(p['tools'])}"); lines.append(p["outcome"] or p["implementation"][:500])
    if profile.get("education"):
        lines.extend(["", "EDUCATION"]); lines.extend(" — ".join(x for x in [i.get("qualification",""), i.get("institution","")] if x) for i in profile["education"])
    if profile.get("certifications"):
        lines.extend(["", "CERTIFICATIONS"]); lines.extend(i.get("name","") for i in profile["certifications"] if i.get("name"))
    changes = [f"Prioritized verified skill: {x}" for x in included[:12]]
    changes += [f"Included portfolio project: {p['title']}" for p in projects]
    changes += [f"Not claimed because unverified: {x}" for x in missing[:12]]
    return lines, included, missing, changes


def generate_tailored_resume(student_id: int, job_id: str, portfolio_build_id: str = "") -> dict[str, Any]:
    profile = get_candidate_profile(student_id)
    if not profile.get("verified"):
        raise ValueError("Verify the candidate profile before generating application documents.")
    job = get_job(student_id, job_id) if job_id else None
    projects = list_portfolio_projects(student_id)
    terms = (job or {}).get("match", {}).get("required_skills", [])
    eligible = [p for p in projects if p["status"] in {"approved", "portfolio_ready", "ready_for_review"} and not p.get("report", {}).get("secret_findings")]
    eligible.sort(key=lambda p: (_project_relevance(p, terms), p["score"]), reverse=True)
    selected = eligible[:4]
    lines, included, missing, changes = _resume_content(profile, job, selected)
    rid = "resumev_" + secrets.token_hex(8)
    folder = CAREER_DIR / f"student_{student_id}" / "resumes"; folder.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9]+", "_", f"{profile.get('full_name','Candidate')}_{(job or {}).get('title','DevOps')}").strip("_")[:100]
    text_file = folder / f"{stem}_{rid[-6:]}.txt"; text_file.write_text("\n".join(lines), encoding="utf-8")
    html_body = "".join(f"<p>{html.escape(line)}</p>" if line and line.isupper() is False else f"<h2>{html.escape(line)}</h2>" if line else "<br>" for line in lines)
    html_file = folder / f"{stem}_{rid[-6:]}.html"; html_file.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>body{{font:11pt Arial;max-width:780px;margin:35px auto;color:#111}}h1,h2{{margin:12px 0 5px}}p{{margin:4px 0}}</style></head><body>{html_body}</body></html>", encoding="utf-8")
    docx_file = folder / f"{stem}_{rid[-6:]}.docx"; make_docx(lines, docx_file)
    pdf_file = folder / f"{stem}_{rid[-6:]}.pdf"; make_simple_pdf(lines, pdf_file, f"{profile.get('full_name','Candidate')} Resume")
    score = (job or {}).get("match_score", 0)
    with _connect() as conn:
        conn.execute("INSERT INTO resume_variants VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (rid, student_id, job_id, f"Tailored resume — {(job or {}).get('title','General DevOps')}", _stored_path(text_file), _stored_path(html_file), _stored_path(docx_file), _stored_path(pdf_file), score, _json(included), _json(missing), _json([p["id"] for p in selected]), _json(changes), now_iso()))
        if job_id: conn.execute("UPDATE job_posts SET status='resume_prepared',updated_at=? WHERE id=? AND student_id=?", (now_iso(), job_id, student_id))
        conn.commit()
    _audit(student_id, "resume_tailored", f"job={job_id};included={len(included)};missing={len(missing)}")
    return get_resume_variant(student_id, rid)


def get_resume_variant(student_id: int, resume_id: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM resume_variants WHERE id=? AND student_id=?", (resume_id, student_id)).fetchone()
    if not row: raise ValueError("Resume variant was not found.")
    d = _row(row) or {}
    for source,target in (("included_keywords_json","included_keywords"),("missing_keywords_json","missing_keywords"),("selected_projects_json","selected_projects"),("change_log_json","change_log")):
        d[target] = _load_json(d.pop(source), [])
    d["links"] = {fmt: f"/api/v4/resume/file?id={resume_id}&format={fmt}" for fmt in ("pdf","docx","html","txt")}
    return d


def list_resume_variants(student_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM resume_variants WHERE student_id=? ORDER BY created_at DESC", (student_id,)).fetchall()]
    return [get_resume_variant(student_id, x) for x in ids]


def resume_variant_file(student_id: int, resume_id: str, fmt: str) -> tuple[Path, str, str, bool]:
    d = get_resume_variant(student_id, resume_id)
    field = {"pdf":"pdf_file","docx":"docx_file","html":"html_file","txt":"text_file"}.get(fmt)
    if not field: raise ValueError("Unsupported resume format.")
    path = _resolved_stored_path(d[field]); root = CAREER_DIR.resolve()
    if root not in path.parents or not path.is_file(): raise ValueError("Resume file is unavailable.")
    mime = {"pdf":"application/pdf","docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","html":"text/html; charset=utf-8","txt":"text/plain; charset=utf-8"}[fmt]
    return path, mime, path.name, fmt in {"pdf","html","txt"}


def _attachment_paths(student_id: int, resume_id: str, portfolio_id: str) -> list[Path]:
    paths: list[Path] = []
    if resume_id: paths.append(resume_variant_file(student_id, resume_id, "pdf")[0])
    if portfolio_id: paths.append(portfolio_file(student_id, portfolio_id, "pdf")[0])
    total = sum(p.stat().st_size for p in paths)
    if total > MAX_EMAIL_ATTACHMENT: raise ValueError("Combined attachments exceed the 12 MB safe email limit.")
    return paths


def create_email_draft(student_id: int, data: dict[str, Any]) -> dict[str, Any]:
    recipient = _validate_email(data.get("recipient"))
    cc = _clean(data.get("cc"), 254)
    if cc: cc = _validate_email(cc)
    subject = _clean(data.get("subject"), 200)
    body = _clean(data.get("body"), 20_000)
    if len(subject) < 3 or len(body) < 20: raise ValueError("Email subject and body are required.")
    job_id = _clean(data.get("job_id"), 100); resume_id = _clean(data.get("resume_variant_id"), 100); portfolio_id = _clean(data.get("portfolio_build_id"), 100)
    if job_id: get_job(student_id, job_id)
    attachments = _attachment_paths(student_id, resume_id, portfolio_id)
    profile = get_candidate_profile(student_id)
    msg = EmailMessage(policy=email.policy.SMTP)
    msg["From"] = profile.get("email") or "candidate@example.invalid"; msg["To"] = recipient
    if cc: msg["Cc"] = cc
    msg["Subject"] = subject; msg.set_content(body)
    for path in attachments:
        mime, _ = mimetypes.guess_type(path.name); major, minor = (mime or "application/octet-stream").split("/",1)
        msg.add_attachment(path.read_bytes(), maintype=major, subtype=minor, filename=path.name)
    did = "mail_" + secrets.token_hex(8); OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    eml = OUTBOX_DIR / f"{did}.eml"; eml.write_bytes(msg.as_bytes())
    with _connect() as conn:
        conn.execute("INSERT INTO email_drafts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (did, student_id, job_id, resume_id, portfolio_id, recipient, cc, subject, body, _json([_stored_path(p) for p in attachments]), _stored_path(eml), "draft", "", now_iso(), ""))
        if job_id: conn.execute("UPDATE job_posts SET status='awaiting_approval',updated_at=? WHERE id=? AND student_id=?", (now_iso(), job_id, student_id))
        conn.commit()
    _audit(student_id, "email_draft_created", f"to={recipient};job={job_id};attachments={len(attachments)}")
    return get_email_draft(student_id, did)


def get_email_draft(student_id: int, draft_id: str) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM email_drafts WHERE id=? AND student_id=?", (draft_id, student_id)).fetchone()
    if not row: raise ValueError("Email draft was not found.")
    data = _row(row) or {}; data["attachments"] = _load_json(data.pop("attachment_json", "[]"), []); data["download"] = f"/api/v4/email/file?id={draft_id}"
    return data


def list_email_drafts(student_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM email_drafts WHERE student_id=? ORDER BY created_at DESC", (student_id,)).fetchall()]
    return [get_email_draft(student_id, x) for x in ids]


def email_draft_file(student_id: int, draft_id: str) -> tuple[Path, str, str, bool]:
    draft = get_email_draft(student_id, draft_id); path = _resolved_stored_path(draft["eml_file"])
    if OUTBOX_DIR.resolve() not in path.parents or not path.is_file(): raise ValueError("Email draft file is unavailable.")
    return path, "message/rfc822", path.name, False


def _protect_bytes(raw: bytes) -> bytes:
    if os.name != "nt": return b"PLAIN-LOCAL-TEST\n" + raw
    import ctypes
    from ctypes import wintypes
    class DATA_BLOB(ctypes.Structure): _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]
    in_buffer = ctypes.create_string_buffer(raw); in_blob = DATA_BLOB(len(raw), ctypes.cast(in_buffer, ctypes.POINTER(ctypes.c_byte))); out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(in_blob), "Billinger Gmail token", None, None, None, 0, ctypes.byref(out_blob)):
        raise OSError("Windows DPAPI could not protect the Gmail token.")
    try: return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally: ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _unprotect_bytes(raw: bytes) -> bytes:
    if raw.startswith(b"PLAIN-LOCAL-TEST\n"): return raw.split(b"\n",1)[1]
    if os.name != "nt": raise ValueError("Encrypted Gmail token can only be opened by the Windows user who created it.")
    import ctypes
    from ctypes import wintypes
    class DATA_BLOB(ctypes.Structure): _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]
    in_buffer = ctypes.create_string_buffer(raw); in_blob = DATA_BLOB(len(raw), ctypes.cast(in_buffer, ctypes.POINTER(ctypes.c_byte))); out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        raise OSError("Windows DPAPI could not open the Gmail token. Reconnect Gmail on this Windows account.")
    try: return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally: ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def save_gmail_client(student_id: int, filename: str, content_base64: str) -> dict[str, Any]:
    if not filename.lower().endswith(".json"): raise ValueError("Upload the OAuth client JSON file downloaded from Google Cloud.")
    raw = base64.b64decode(content_base64, validate=True)
    if len(raw) > 256_000: raise ValueError("OAuth client file is unexpectedly large.")
    payload = json.loads(raw.decode("utf-8")); config = payload.get("installed") or payload.get("web")
    if not isinstance(config, dict) or not config.get("client_id") or not config.get("client_secret"):
        raise ValueError("OAuth client JSON is missing installed/web client credentials.")
    client_id = _clean(config.get("client_id"), 300)
    client_secret = _clean(config.get("client_secret"), 500)
    if not client_id.endswith(".apps.googleusercontent.com") or len(client_secret) < 8:
        raise ValueError("OAuth client credentials do not match a Google OAuth client.")
    # Never trust endpoint overrides from an uploaded file. Pin OAuth traffic to Google's official endpoints.
    safe = {"client_id": client_id, "client_secret": client_secret, "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth", "token_uri": "https://oauth2.googleapis.com/token"}
    folder = TOKEN_DIR / f"student_{student_id}"; folder.mkdir(parents=True, exist_ok=True)
    (folder / "gmail_client.json").write_bytes(_protect_bytes(_json(safe).encode()))
    return {"configured": True, "client_id_suffix": safe["client_id"][-12:]}


def _gmail_config(student_id: int) -> dict[str, Any]:
    path = TOKEN_DIR / f"student_{student_id}" / "gmail_client.json"
    if not path.is_file(): raise ValueError("Gmail OAuth client is not configured.")
    return json.loads(_unprotect_bytes(path.read_bytes()).decode())


def gmail_auth_start(student_id: int, redirect_uri: str) -> dict[str, Any]:
    config = _gmail_config(student_id); redirect_uri = _clean(redirect_uri, 500)
    parsed = urllib.parse.urlparse(redirect_uri)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.path != "/oauth/gmail/callback":
        raise ValueError("Gmail callback must use this bot's localhost OAuth callback.")
    state = secrets.token_urlsafe(24); OAUTH_STATES[state] = (student_id, dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=10), redirect_uri)
    params = {"client_id":config["client_id"],"redirect_uri":redirect_uri,"response_type":"code","scope":"https://www.googleapis.com/auth/gmail.send","access_type":"offline","prompt":"consent","state":state,"include_granted_scopes":"true"}
    return {"authorization_url": config["auth_uri"] + "?" + urllib.parse.urlencode(params), "state": state}


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    if url != "https://oauth2.googleapis.com/token":
        raise ValueError("OAuth token exchange is restricted to Google's official token endpoint.")
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers={"Content-Type":"application/x-www-form-urlencoded","User-Agent":f"BillingerBot/{VERSION}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp: return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError) as exc: raise ValueError(f"OAuth request failed: {exc}") from exc


def gmail_oauth_callback(code: str, state: str, poster: Callable[[str,dict[str,str]],dict[str,Any]] = _post_form) -> dict[str, Any]:
    entry = OAUTH_STATES.pop(_clean(state, 200), None)
    if not entry or entry[1] < dt.datetime.now(dt.timezone.utc): raise PermissionError("OAuth state is invalid or expired.")
    student_id, _, redirect_uri = entry; config = _gmail_config(student_id)
    token = poster(config["token_uri"], {"code":_clean(code,2000),"client_id":config["client_id"],"client_secret":config["client_secret"],"redirect_uri":redirect_uri,"grant_type":"authorization_code"})
    if not token.get("access_token"): raise ValueError("Google did not return an access token.")
    token["obtained_at"] = now_iso(); token["expires_at_epoch"] = int(dt.datetime.now().timestamp()) + int(token.get("expires_in",3600))
    folder = TOKEN_DIR / f"student_{student_id}"; folder.mkdir(parents=True, exist_ok=True); (folder/"gmail_token.bin").write_bytes(_protect_bytes(_json(token).encode()))
    _audit(student_id, "gmail_connected", "gmail.send OAuth scope granted")
    return {"connected": True, "student_id": student_id, "scope": token.get("scope", "gmail.send")}


def gmail_status(student_id: int) -> dict[str, Any]:
    folder = TOKEN_DIR / f"student_{student_id}"
    return {"client_configured": (folder/"gmail_client.json").is_file(), "connected": (folder/"gmail_token.bin").is_file(), "storage": "Windows DPAPI" if os.name=="nt" else "test-environment fallback"}


def _load_gmail_token(student_id: int) -> dict[str, Any]:
    path = TOKEN_DIR / f"student_{student_id}" / "gmail_token.bin"
    if not path.is_file(): raise ValueError("Gmail is not connected.")
    token = json.loads(_unprotect_bytes(path.read_bytes()).decode())
    if int(token.get("expires_at_epoch",0)) < int(dt.datetime.now().timestamp()) + 60:
        if not token.get("refresh_token"): raise ValueError("Gmail authorization expired. Reconnect Gmail.")
        config = _gmail_config(student_id); refreshed = _post_form(config["token_uri"], {"client_id":config["client_id"],"client_secret":config["client_secret"],"refresh_token":token["refresh_token"],"grant_type":"refresh_token"})
        token.update(refreshed); token["expires_at_epoch"] = int(dt.datetime.now().timestamp()) + int(refreshed.get("expires_in",3600)); path.write_bytes(_protect_bytes(_json(token).encode()))
    return token


def _gmail_send_raw(access_token: str, raw_urlsafe: str) -> dict[str, Any]:
    body = json.dumps({"raw": raw_urlsafe}).encode()
    req = urllib.request.Request("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", data=body, method="POST", headers={"Authorization":f"Bearer {access_token}","Content-Type":"application/json","User-Agent":f"BillingerBot/{VERSION}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp: return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="ignore")
        raise ValueError(f"Gmail send failed ({exc.code}): {detail[:500]}") from exc
    except urllib.error.URLError as exc: raise ValueError(f"Gmail send failed: {exc}") from exc


def send_email_draft(student_id: int, draft_id: str, confirmation: str, sender: Callable[[str,str],dict[str,Any]] = _gmail_send_raw) -> dict[str, Any]:
    if confirmation != "SEND": raise PermissionError("Sending requires the exact confirmation word SEND.")
    now = dt.datetime.now(dt.timezone.utc); events = [x for x in SEND_EVENTS.get(student_id,[]) if (now-x).total_seconds()<86400]; SEND_EVENTS[student_id]=events
    hour_cutoff = (now - dt.timedelta(hours=1)).isoformat(timespec="seconds")
    day_cutoff = (now - dt.timedelta(days=1)).isoformat(timespec="seconds")
    with _connect() as conn:
        sent_hour = int(conn.execute("SELECT COUNT(*) FROM email_drafts WHERE student_id=? AND status='sent' AND sent_at>=?", (student_id, hour_cutoff)).fetchone()[0])
        sent_day = int(conn.execute("SELECT COUNT(*) FROM email_drafts WHERE student_id=? AND status='sent' AND sent_at>=?", (student_id, day_cutoff)).fetchone()[0])
    if max(sent_hour, len([x for x in events if (now-x).total_seconds()<3600])) >= 10 or max(sent_day, len(events)) >= 50:
        raise PermissionError("Email safety rate limit reached. Wait before sending more applications.")
    draft = get_email_draft(student_id, draft_id)
    if draft["status"] == "sent": raise ValueError("This email draft was already sent.")
    token = _load_gmail_token(student_id); eml = _resolved_stored_path(draft["eml_file"]).read_bytes(); raw = base64.urlsafe_b64encode(eml).decode().rstrip("=")
    result = sender(token["access_token"], raw); message_id = _clean(result.get("id"), 200)
    if not message_id: raise ValueError("Gmail did not confirm the sent message.")
    sent_at = now_iso(); app_id = "app_" + secrets.token_hex(8)
    with _connect() as conn:
        conn.execute("UPDATE email_drafts SET status='sent',gmail_message_id=?,sent_at=? WHERE id=? AND student_id=?", (message_id,sent_at,draft_id,student_id))
        if draft["job_id"]:
            conn.execute("UPDATE job_posts SET status='applied',updated_at=? WHERE id=? AND student_id=?", (sent_at,draft["job_id"],student_id))
            conn.execute("INSERT INTO job_applications VALUES(?,?,?,?,?,?,?,?,?,?,?)", (app_id,student_id,draft["job_id"],draft["resume_variant_id"],draft["portfolio_build_id"],draft_id,"applied",sent_at,(dt.date.today()+dt.timedelta(days=7)).isoformat(),"Sent through Gmail API after explicit approval",sent_at))
        conn.commit()
    SEND_EVENTS[student_id].append(now); _audit(student_id,"application_email_sent",f"draft={draft_id};gmail_id={message_id}")
    return {"sent": True, "gmail_message_id": message_id, "sent_at": sent_at, "application_id": app_id if draft["job_id"] else ""}


def mark_assisted_application(student_id: int, job_id: str, resume_id: str = "", portfolio_id: str = "", notes: str = "") -> dict[str, Any]:
    get_job(student_id, job_id)
    app_id = "app_" + secrets.token_hex(8); ts = now_iso()
    with _connect() as conn:
        conn.execute("INSERT INTO job_applications VALUES(?,?,?,?,?,?,?,?,?,?,?)", (app_id,student_id,job_id,resume_id,portfolio_id,"","assisted_application",ts,(dt.date.today()+dt.timedelta(days=7)).isoformat(),_clean(notes,4000),ts))
        conn.execute("UPDATE job_posts SET status='assisted_application',updated_at=? WHERE id=? AND student_id=?", (ts,job_id,student_id)); conn.commit()
    return {"id":app_id,"status":"assisted_application","applied_at":ts}


def list_applications(student_id: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("""SELECT a.*,j.company,j.title,j.url,j.match_score FROM job_applications a JOIN job_posts j ON j.id=a.job_id WHERE a.student_id=? ORDER BY a.updated_at DESC""",(student_id,)).fetchall()
    return [_row(r) or {} for r in rows]


def research_and_prepare_interview(student_id: int, job_id: str, company_url: str = "", fetcher: Callable[..., tuple[bytes,str,str]] = safe_fetch) -> dict[str, Any]:
    job = get_job(student_id, job_id); profile = get_candidate_profile(student_id); projects = list_portfolio_projects(student_id)
    company_summary = "Research is based on the supplied job description and general role expectations."
    basis = ["Job description", "Verified candidate profile", "Verified portfolio projects", "General role-based interview patterns"]
    source_url = ""
    if company_url:
        source_url = _validate_public_url(company_url)
        if not _robots_allows(source_url, fetcher): raise ValueError("robots.txt does not permit automated access to the company URL.")
        raw, _, final = fetcher(source_url, "text/html", MAX_REMOTE_BYTES); source_url = final; text = _strip_html(raw.decode("utf-8",errors="ignore"))
        company_summary = text[:2500]; basis.insert(0,"Public company website")
    terms = job.get("match",{}).get("required_skills",[]) or _extract_terms(job["description"])
    relevant_projects = sorted(projects,key=lambda p:_project_relevance(p,terms),reverse=True)[:4]
    rounds = ["Recruiter screening","HR and motivation","Linux and networking","DevOps tools","Live troubleshooting","Scripting or coding","System design","Managerial and incident response","Final HR and compensation"]
    questions = [f"Explain your practical experience with {term} and the evidence you can show." for term in terms[:10]]
    for p in relevant_projects:
        questions += [f"Your portfolio lists '{p['title']}'. What business problem did it solve?", f"How did you validate and roll back '{p['title']}'?", f"Which part of '{p['title']}' was simulated, guided, or independently implemented?"]
    questions += ["Describe a production-style incident, your evidence-gathering sequence, and your stakeholder communication.","Which requirement in this job description is currently your largest gap, and how are you closing it?"]
    report_id = "research_" + secrets.token_hex(8)
    with _connect() as conn:
        conn.execute("INSERT INTO research_reports VALUES(?,?,?,?,?,?,?,?,?,?)", (report_id,student_id,job_id,source_url,company_summary,"; ".join(basis),_json(rounds),_json(terms[:30]),_json(questions[:40]),now_iso())); conn.commit()
    return {"id":report_id,"job":job,"company_summary":company_summary,"source_url":source_url,"evidence_basis":basis,"likely_rounds":rounds,"topics":terms[:30],"questions":questions[:40],"warning":"Reported or inferred interview stages are preparation guidance, not a guarantee of the company's current process.","recruitment_payload":{"target_role":job["title"],"track":"full-devops","difficulty":"Intermediate","resume_text":profile.get("master_resume_text",profile.get("summary","")),"job_description":job["description"]}}


def career_dashboard(student_id: int) -> dict[str, Any]:
    profile = get_candidate_profile(student_id)
    jobs = list_jobs(student_id); projects = list_portfolio_projects(student_id); builds = list_portfolio_builds(student_id); resumes = list_resume_variants(student_id); drafts = list_email_drafts(student_id); applications = list_applications(student_id)
    return {"version":VERSION,"profile":profile,"gmail":gmail_status(student_id),"sources":list_job_sources(student_id),"jobs":jobs,"projects":projects,"portfolio_builds":builds,"resume_variants":resumes,"email_drafts":drafts,"applications":applications,"summary":{"jobs":len(jobs),"recommended":sum(1 for x in jobs if x["match_score"]>=75),"portfolio_ready":sum(1 for x in projects if x["status"] in {"approved","portfolio_ready"}),"applications":len(applications),"offers":sum(1 for x in applications if x["status"]=="offer")},"operating_model":"Discover → explain match → tailor truthfully → preview → approve → send/apply → track → research → mock interview"}


def system_requirements() -> dict[str, Any]:
    return {"minimum_ram_gb":4,"recommended_ram_gb":8,"typical_core_ram_mb":"400–900 including one browser tab","minimum_free_space_mb":750,"recommended_long_term_space_gb":"5–15","gpu_required":False,"internet":"Required only for job discovery, company research, Gmail OAuth, and sending","optional_local_ai":"Adds approximately 2–10 GB RAM and 1.5–6 GB storage depending on model"}
