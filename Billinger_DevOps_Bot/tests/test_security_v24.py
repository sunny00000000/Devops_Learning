from __future__ import annotations

import base64
import io
import json
import os
import pathlib
import sqlite3
import tempfile
import unittest
import zipfile
from unittest import mock

import app
import v2_features as v2
import v23_features as v23
import v24_features as v24


PROFILE = {
    "full_name": "Security Tester",
    "email": "security@example.com",
    "headline": "DevOps Engineer",
    "summary": "Verified Linux Git Docker Jenkins AWS automation profile.",
    "skills": ["Linux", "Git", "Docker", "Jenkins", "AWS"],
    "experience": [{"role": "DevOps Trainee", "company": "Training Lab", "years": "1", "details": "Built validated pipelines."}],
    "education": [], "certifications": [], "preferences": {}, "links": {},
    "master_resume_text": "Linux Git Docker Jenkins AWS automation", "verified": True,
}


class SecurityV24Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        db = root / "billinger.db"
        app.DB_PATH = db; app.v2.DB_PATH = db; app.v23.DB_PATH = db; app.v24.DB_PATH = db
        v2.DB_PATH = db; v2.LAB_DIR = root / "labs"
        v23.DB_PATH = db; v23.WORKSPACE_DIR = root / "workspaces"; v23.CERT_DIR = root / "certificates"
        v23.BACKUP_DIR = root / "backups"; v23.IMPORT_DIR = root / "imports"; v23.UPDATE_DIR = root / "updates"
        v24.BASE_DIR = root; v24.DATA_DIR = root / "data"; v24.CAREER_DIR = root / "career_data"
        v24.PORTFOLIO_DIR = root / "portfolios"; v24.OUTBOX_DIR = root / "mail_outbox"; v24.TOKEN_DIR = root / "tokens"; v24.DB_PATH = db
        v23._ADMIN_TOKENS.clear(); v23._ADMIN_FAILURES.clear()
        v24.STUDENT_SESSIONS.clear(); v24.AUTH_FAILURES.clear(); v24.SEND_EVENTS.clear(); v24.OAUTH_STATES.clear()
        app.init_db()
        self.sid = 1
        v24.save_candidate_profile(self.sid, PROFILE)

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _b64_zip(entries: list[tuple[str, bytes, int | None]]) -> str:
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, raw, external_attr in entries:
                info = zipfile.ZipInfo(name)
                info.compress_type = zipfile.ZIP_DEFLATED
                if external_attr is not None:
                    info.create_system = 3
                    info.external_attr = external_attr
                zf.writestr(info, raw)
        return base64.b64encode(out.getvalue()).decode()

    def test_zip_slip_rejected_for_import_restore_and_update(self):
        malicious = self._b64_zip([("../escape.txt", b"owned", None)])
        with self.assertRaises(ValueError): v23.stage_content_import("bad.zip", malicious)
        with self.assertRaises(ValueError): v23.stage_restore("bad.zip", malicious)
        with self.assertRaises(ValueError): v23.stage_offline_update("bad.zip", malicious)
        self.assertFalse((pathlib.Path(self.tmp.name).parent / "escape.txt").exists())

    def test_zip_symlink_rejected(self):
        # POSIX symlink file type plus permissive mode.
        symlink_attr = (0o120777 << 16)
        payload = self._b64_zip([("link", b"../../outside", symlink_attr)])
        with self.assertRaises(ValueError): v23.stage_offline_update("symlink.zip", payload)

    def test_zip_bomb_ratio_rejected(self):
        payload = self._b64_zip([("Billinger_DevOps_Bot/VERSION.txt", b"2.5.1", None), ("Billinger_DevOps_Bot/blob.txt", b"A" * (2 * 1024 * 1024), None)])
        with self.assertRaisesRegex(ValueError, "compression ratio"):
            v23.stage_offline_update("bomb.zip", payload)

    def test_admin_bruteforce_rate_limit(self):
        v23.admin_setup("2468", "Admin", "Institute")
        for _ in range(8):
            with self.assertRaises(ValueError): v23.admin_auth("wrong")
        with self.assertRaises(PermissionError): v23.admin_auth("2468")

    def test_lab_command_injection_and_traversal_blocked(self):
        attacks = [
            "git clean -fdx", "git status && whoami", "kubectl get secrets", "python -c print(1)",
            "cat ../../etc/passwd", "rm -rf .", "docker rm all", "sudo whoami", "echo hi > stolen.txt",
        ]
        for command in attacks:
            with self.subTest(command=command):
                with self.assertRaises(ValueError): v2.run_lab_command(self.sid, command, "simulator")

    def test_stored_xss_is_escaped_in_generated_portfolio(self):
        project = {
            "title": "<script>alert(1)</script>", "origin": "Independent project", "level": "Intermediate",
            "tools": ["Docker"], "problem_statement": "<img src=x onerror=alert(2)>",
            "business_requirement": "Safe delivery", "architecture": "Git to Docker", "responsibilities": "Built it",
            "implementation": "Created a container pipeline, immutable tags, release gates, and validated each delivery stage with repeatable commands and documented evidence.", "security_controls": "Used least privilege, no embedded secrets, image scanning, and protected credentials.",
            "testing": "Ran unit, integration, container health, and release smoke tests", "monitoring": "Health checks, service metrics, and deployment alerts", "troubleshooting": "Reviewed logs, formed a hypothesis, corrected configuration, and retested",
            "rollback": "Redeployed the last known-good immutable image and verified service health", "outcome": "Delivered a validated repeatable release with documented recovery", "evidence": ["test output", "pipeline log", "image digest", "health response", "rollback record"], "status": "approved",
        }
        v24.save_portfolio_project(self.sid, project)
        build = v24.generate_portfolio(self.sid, {})
        html_text = v24._resolved_stored_path(build["website_file"]).read_text(encoding="utf-8")
        self.assertNotIn("<script>alert(1)</script>", html_text)
        self.assertNotIn("<img src=x onerror=alert(2)>", html_text)
        self.assertIn("&lt;script&gt;", html_text)

    def test_sql_injection_input_does_not_change_schema(self):
        payload = "DevOps'); DROP TABLE students; --"
        job = v24.analyze_manual_job(self.sid, {"company": payload, "title": payload, "description": "Linux Docker Jenkins AWS security monitoring and rollback role with sufficient detail."})
        self.assertIn("DROP TABLE", job["company"])
        conn = sqlite3.connect(v24.DB_PATH)
        try:
            count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        finally:
            conn.close()
        self.assertGreaterEqual(count, 1)

    def test_public_url_validation_blocks_private_and_credential_urls(self):
        attacks = [
            "http://127.0.0.1/admin", "https://localhost/", "file:///etc/passwd", "ftp://example.com/a",
            "https://user:pass@example.com/jobs", "https://[::1]/", "https://169.254.169.254/latest/meta-data/",
        ]
        for url in attacks:
            with self.subTest(url=url):
                with self.assertRaises(ValueError): v24._validate_public_url(url)

    def test_oauth_state_is_single_use(self):
        client = {"installed": {"client_id": "abc.apps.googleusercontent.com", "client_secret": "secret-value", "auth_uri": "https://evil.example/authorize", "token_uri": "https://evil.example/token"}}
        v24.save_gmail_client(self.sid, "client.json", base64.b64encode(json.dumps(client).encode()).decode())
        config = v24._gmail_config(self.sid)
        self.assertEqual(config["auth_uri"], "https://accounts.google.com/o/oauth2/v2/auth")
        self.assertEqual(config["token_uri"], "https://oauth2.googleapis.com/token")
        start = v24.gmail_auth_start(self.sid, "http://127.0.0.1:8765/oauth/gmail/callback")
        v24.gmail_oauth_callback("code", start["state"], lambda u,d: {"access_token":"a","refresh_token":"r","expires_in":3600,"scope":"gmail.send"})
        with self.assertRaises(PermissionError):
            v24.gmail_oauth_callback("code2", start["state"], lambda u,d: {})

    def test_email_headers_and_attachment_ownership(self):
        with self.assertRaises(ValueError):
            v24.create_email_draft(self.sid, {"recipient":"hr@example.com\r\nCc:evil@example.com", "subject":"Job", "body":"A valid application body long enough for validation."})
        with app.db_connect() as conn:
            ts = app.now_iso(); conn.execute("INSERT INTO students(name,email,pin_hash,created_at,last_active) VALUES(?,?,?,?,?)", ("Other","",app.hash_pin("1234"),ts,ts))
            other = int(conn.execute("SELECT max(id) FROM students").fetchone()[0])
        v24.save_candidate_profile(other, dict(PROFILE, full_name="Other", email="other@example.com"))
        job = v24.analyze_manual_job(other, {"company":"Acme","title":"DevOps","description":"Linux Docker Jenkins AWS monitoring security rollback and validation requirements."})
        resume = v24.generate_tailored_resume(other, job["id"])
        with self.assertRaises(ValueError):
            v24.create_email_draft(self.sid, {"recipient":"hr@example.com", "subject":"Application", "body":"A valid application message for a role.", "resume_variant_id":resume["id"]})

    def test_student_session_cannot_cross_student_boundary(self):
        with app.db_connect() as conn:
            ts=app.now_iso(); conn.execute("INSERT INTO students(name,email,pin_hash,created_at,last_active) VALUES(?,?,?,?,?)", ("Other","",app.hash_pin("1234"),ts,ts)); other=int(conn.execute("SELECT max(id) FROM students").fetchone()[0])
        token = v24.create_student_session(self.sid, "", app.verify_pin)["token"]
        v24.require_student(token, self.sid)
        with self.assertRaises(PermissionError): v24.require_student(token, other)

    def test_secret_scanner_detects_common_credentials(self):
        text = "AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF\npassword=SuperSecret123!\ngithub_pat_11AAABBBCCC1234567890"
        findings = v24.scan_secrets(text)
        self.assertGreaterEqual(len(findings), 2)
        self.assertNotIn("SuperSecret123", json.dumps(findings))


if __name__ == "__main__":
    unittest.main()
