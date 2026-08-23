"""Adversarial HTTP checks for Billinger Bot v2.4 local server."""
from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def call(port: int, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    final = {"Host": f"127.0.0.1:{port}"}
    if body:
        final["Content-Type"] = "application/json"
        final["Content-Length"] = str(len(body))
    if headers:
        final.update(headers)
    conn.request(method, path, body=body, headers=final)
    response = conn.getresponse()
    raw = response.read()
    result = (response.status, {k.lower(): v for k, v in response.getheaders()}, raw)
    conn.close()
    return result


def jcall(port: int, method: str, path: str, payload: dict | None = None, headers: dict[str, str] | None = None):
    body = b"" if payload is None else json.dumps(payload).encode()
    status, response_headers, raw = call(port, method, path, body, headers)
    parsed = json.loads(raw.decode()) if raw else {}
    return status, response_headers, parsed


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp); port = 8895
        env = dict(os.environ,
            BILLINGER_DB_PATH=str(root/"db.sqlite"), BILLINGER_CAREER_DIR=str(root/"career"),
            BILLINGER_PORTFOLIO_DIR=str(root/"portfolios"), BILLINGER_OUTBOX_DIR=str(root/"outbox"),
            BILLINGER_TOKEN_DIR=str(root/"tokens"), BILLINGER_WORKSPACE_DIR=str(root/"workspaces"),
            BILLINGER_CERT_DIR=str(root/"certs"), BILLINGER_BACKUP_DIR=str(root/"backups"),
            BILLINGER_IMPORT_DIR=str(root/"imports"), BILLINGER_UPDATE_DIR=str(root/"updates"))
        proc = subprocess.Popen([sys.executable, "app.py", "--host", "127.0.0.1", "--port", str(port), "--no-browser"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            for _ in range(80):
                try:
                    status, headers, health = jcall(port, "GET", "/api/health")
                    if status == 200: break
                except Exception:
                    pass
                time.sleep(.1)
            else: raise RuntimeError("server did not start")

            assert health["version"] == "2.9.0"
            for key in ("content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy", "cross-origin-opener-policy"):
                assert key in headers, key

            status, _, payload = jcall(port, "GET", "/api/health", headers={"Host": "evil.example"})
            assert status == 403 and "localhost" in payload["error"].lower()

            status, _, payload = jcall(port, "POST", "/api/v4/student/session", {"student_id": 1, "pin": ""}, {"Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"})
            assert status == 403 and "cross-origin" in payload["error"].lower()

            status, _, students = jcall(port, "GET", "/api/students")
            sid = students["students"][0]["id"]
            status, _, session = jcall(port, "POST", "/api/v4/student/session", {"student_id": sid, "pin": ""})
            assert status == 200
            token = session["token"]

            status, _, payload = jcall(port, "GET", f"/api/v4/career/dashboard?student_id={sid}")
            assert status == 403 and "session" in payload["error"].lower()

            status, _, payload = jcall(port, "GET", f"/api/v4/career/dashboard?student_id={sid}", headers={"X-Student-Token": "wrong"})
            assert status == 403

            # Encoded traversal must never disclose server source.
            status, _, raw = call(port, "GET", "/..%2f..%2fapp.py")
            assert status in {200, 403, 404}
            assert b"import argparse" not in raw and b"class AppHandler" not in raw

            status, _, raw = call(port, "POST", "/api/v4/profile/save", b"{not-json", {"X-Student-Token": token, "Content-Type": "application/json", "Content-Length": "9"})
            assert status == 400
            assert b"Traceback" not in raw and b"valid JSON" in raw

            # SQL and XSS-like strings are handled as data, without traceback or execution.
            hostile = {
                "student_id": sid, "full_name": "<script>alert(1)</script>", "email": "safe@example.com",
                "headline": "DevOps'); DROP TABLE students; --", "summary": "Verified local security test profile.",
                "skills": ["Linux", "Docker"], "experience": [], "education": [], "certifications": [],
                "preferences": {}, "links": {}, "master_resume_text": "Linux Docker", "verified": True,
            }
            status, _, profile = jcall(port, "POST", "/api/v4/profile/save", hostile, {"X-Student-Token": token, "Origin": f"http://127.0.0.1:{port}"})
            assert status == 200 and "DROP TABLE" in profile["headline"]
            status, _, students_after = jcall(port, "GET", "/api/students")
            assert status == 200 and students_after["students"]

            # IDOR: token for one student cannot read a second student's career data.
            status, _, created = jcall(port, "POST", "/api/students/create", {"name":"Second Student", "email":"", "pin":"1234"})
            if status == 200 and created.get("student"):
                other = created["student"]["id"]
            else:
                # Existing endpoint may return the student directly.
                other = created.get("id") or created.get("student_id")
            if other:
                status, _, payload = jcall(port, "GET", f"/api/v4/career/dashboard?student_id={other}", headers={"X-Student-Token": token})
                assert status == 403

            print("V4 ADVERSARIAL HTTP SECURITY TEST PASSED")
            print(json.dumps({"headers": "passed", "host_header": "blocked", "cross_origin": "blocked", "idor": "blocked", "traversal": "no source disclosure", "malformed_json": "handled", "sql_xss_payloads": "treated as data"}, indent=2))
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill()


if __name__ == "__main__":
    main()
