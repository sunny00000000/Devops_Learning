"""End-to-end HTTP smoke test for Billinger Bot v2.5.1.

The test uses temporary database and artifact directories, so it leaves the
packaged application clean.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def request(url: str, payload: dict | None = None, token: str = "") -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Admin-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env = dict(
            os.environ,
            BILLINGER_DB_PATH=str(root / "smoke_v3.db"),
            BILLINGER_WORKSPACE_DIR=str(root / "workspaces"),
            BILLINGER_CERT_DIR=str(root / "certificates"),
            BILLINGER_BACKUP_DIR=str(root / "backups"),
            BILLINGER_IMPORT_DIR=str(root / "imports"),
            BILLINGER_UPDATE_DIR=str(root / "updates"),
        )
        port = 8892
        proc = subprocess.Popen(
            [sys.executable, "app.py", "--host", "127.0.0.1", "--port", str(port), "--no-browser"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(80):
                try:
                    health = request(base + "/api/health")
                    break
                except Exception:
                    time.sleep(0.1)
            else:
                raise RuntimeError("server did not start")

            students = request(base + "/api/students")["students"]
            sid = students[0]["id"]
            setup = request(base + "/api/v3/admin/setup", {
                "pin": "2468", "admin_name": "Trainer", "institute_name": "Billinger Test Academy"
            })
            token = setup["token"]
            batch = request(base + "/api/v3/admin/batch/save", {
                "name": "Batch A", "description": "Beginner cohort",
                "target_role": "Junior DevOps Engineer", "level": "Beginner", "deadline": "2026-08-31"
            }, token)
            request(base + "/api/v3/admin/batch/member", {
                "batch_id": batch["id"], "student_id": sid, "assigned": True
            }, token)
            request(base + "/api/v3/admin/assignment/create", {
                "batch_id": batch["id"], "title": "Linux practical",
                "item_type": "practical_exam", "item_id": "linux-beginner",
                "due_date": "2026-08-10", "instructions": "Submit evidence and rollback steps."
            }, token)
            request(base + "/api/v3/admin/announcement/create", {
                "batch_id": batch["id"], "title": "Welcome", "message": "Start with today's plan."
            }, token)

            hub = request(base + f"/api/v3/student/hub?student_id={sid}")
            templates = request(base + "/api/v3/practical/templates?tool=linux&level=Beginner")["templates"]
            run = request(base + "/api/v3/practical/start", {"student_id": sid, "exam_code": templates[0]["exam_code"]})
            response = (
                "Assess business impact and inspect logs, metrics, configuration and permissions. "
                "Form a root-cause hypothesis, implement the smallest safe change, preserve a backup, "
                "validate with test output and health checks, apply least privilege, document evidence, "
                "prepare rollback steps and communicate status to stakeholders. "
            ) * 4
            practical = request(base + "/api/v3/practical/submit", {
                "student_id": sid, "run_id": run["run_id"], "response": response
            })
            saved = request(base + "/api/v3/workspace/save", {
                "student_id": sid, "path": "linux/evidence.md", "content": response, "tool": "linux"
            })
            workspace = request(base + f"/api/v3/workspace?student_id={sid}")
            cert = request(base + "/api/v3/certificate/issue", {
                "student_id": sid, "certificate_type": "Practical Excellence",
                "subject": "Linux Beginner", "score": practical["score"]
            }, token)
            verified = request(base + "/api/v3/certificate/verify?code=" + cert["verification_code"])
            backup = request(base + "/api/v3/admin/backup/create", {}, token)
            overview = request(base + "/api/v3/admin/overview", token=token)

            assert health["version"] == "2.9.0"
            assert len(hub["roadmap"]["items"]) == 21
            assert len(hub["today"]["items"]) >= 1
            assert len(hub["batches"]) == 1 and len(hub["assignments"]) == 1
            assert len(templates) == 1
            assert practical["score"] >= 60
            assert saved["saved"] and len(workspace["files"]) == 1
            assert verified["valid"] is True
            assert backup["size_bytes"] > 0
            assert overview["summary"]["active_students"] >= 1

            print("V3 TRAINING INSTITUTE SMOKE TEST PASSED")
            print(json.dumps({
                "version": health["version"],
                "roadmap_tools": len(hub["roadmap"]["items"]),
                "practical_score": practical["score"],
                "workspace_files": len(workspace["files"]),
                "certificate": cert["verification_code"],
                "backup_bytes": backup["size_bytes"],
            }, indent=2))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
