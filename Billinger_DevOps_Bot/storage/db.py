import sqlite3
import threading
import json
import os
from pathlib import Path
from core.configuration.config import Config
from core.logging.logger import logger

class Database:
    _local = threading.local()

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        Config.ensure_directories()
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            try:
                self._local.conn.execute("PRAGMA journal_mode=MEMORY;")
            except Exception:
                pass
            try:
                self._local.conn.execute("PRAGMA foreign_keys=ON;")
            except Exception:
                pass
        return self._local.conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor

    def fetchone(self, sql: str, params: tuple = ()):
        cursor = self.get_connection().cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()):
        cursor = self.get_connection().cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def init_schema(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=MEMORY;")
        except Exception:
            pass
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                full_name TEXT,
                created_at REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tool_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                mastery_level TEXT DEFAULT 'Beginner',
                commands_mastered TEXT DEFAULT '[]',
                concepts_mastered TEXT DEFAULT '[]',
                knowledge_score REAL DEFAULT 0.0,
                practical_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'in_progress',
                last_updated REAL NOT NULL,
                UNIQUE(user_id, tool_id, module_id)
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                command TEXT NOT NULL,
                tool TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL,
                output TEXT,
                mistakes_detected TEXT,
                timestamp REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                percentage REAL NOT NULL,
                passed INTEGER NOT NULL,
                gaps_json TEXT,
                remediation_json TEXT,
                timestamp REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS lab_runs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                scenario_type TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL DEFAULT 0.0,
                evaluation_json TEXT,
                duration_seconds REAL,
                timestamp REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS incident_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                acknowledged_time REAL,
                resolved_time REAL,
                mttr_seconds REAL,
                status TEXT NOT NULL,
                postmortem_json TEXT,
                timestamp REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                persona TEXT NOT NULL,
                target_company TEXT,
                transcript_json TEXT,
                readiness_score REAL DEFAULT 0.0,
                feedback_json TEXT,
                timestamp REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                domain TEXT NOT NULL,
                primary_tool TEXT NOT NULL,
                confidence REAL NOT NULL,
                version TEXT NOT NULL,
                duplicate_status TEXT NOT NULL,
                content_text TEXT,
                ingested_at REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS career_applications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                company TEXT NOT NULL,
                role_title TEXT NOT NULL,
                job_description TEXT,
                match_score REAL DEFAULT 0.0,
                missing_skills TEXT,
                tailored_resume_path TEXT,
                status TEXT DEFAULT 'drafted',
                created_at REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                technologies TEXT,
                problem_statement TEXT,
                architecture_solution TEXT,
                evidence_log TEXT,
                lessons_learned TEXT,
                created_at REAL NOT NULL
            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_providers (\n                provider_name TEXT PRIMARY KEY,\n                enabled INTEGER DEFAULT 1,\n                api_key TEXT,\n                model TEXT NOT NULL,\n                priority INTEGER DEFAULT 1,\n                status TEXT DEFAULT 'READY',\n                cooldown_until REAL DEFAULT 0.0,\n                last_error TEXT\n            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_telemetry (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                provider TEXT NOT NULL,\n                workload TEXT NOT NULL,\n                latency_ms REAL NOT NULL,\n                status TEXT NOT NULL,\n                tokens_used INTEGER DEFAULT 0,\n                timestamp REAL NOT NULL\n            );""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                event_type TEXT NOT NULL,\n                actor TEXT NOT NULL,\n                details TEXT,\n                timestamp REAL NOT NULL\n            );""")
        conn.close()
        logger.info(f"Database schema verified at {self.db_path}")

db = Database()
