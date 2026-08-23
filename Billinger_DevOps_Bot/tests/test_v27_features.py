from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sqlite3
import tempfile
import unittest
from unittest import mock

import app
import v23_features as v23
import v26_features as v26
import v27_features as v27


class V27FinalReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.tmp.name)
        cls.old = {
            "app_db": app.DB_PATH,
            "v23_db": v23.DB_PATH,
            "v23_backup": v23.BACKUP_DIR,
            "v23_workspace": v23.WORKSPACE_DIR,
            "v23_cert": v23.CERT_DIR,
            "v26_db": v26.DB_PATH,
            "v27_db": v27.DB_PATH,
            "v27_data": v27.DATA_DIR,
            "v27_backup": v27.BACKUP_DIR,
        }
        db = cls.root / "billinger.db"
        app.DB_PATH = db
        v23.DB_PATH = db
        v26.DB_PATH = db
        v27.DB_PATH = db
        v27.DATA_DIR = cls.root / "data"
        v23.BACKUP_DIR = v27.BACKUP_DIR = cls.root / "backups"
        v23.WORKSPACE_DIR = cls.root / "workspaces"
        v23.CERT_DIR = cls.root / "certificates"
        app.init_db()
        with app.db_connect() as conn:
            cls.student_id = int(conn.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()[0])

    @classmethod
    def tearDownClass(cls):
        app.DB_PATH = cls.old["app_db"]
        v23.DB_PATH = cls.old["v23_db"]
        v23.BACKUP_DIR = cls.old["v23_backup"]
        v23.WORKSPACE_DIR = cls.old["v23_workspace"]
        v23.CERT_DIR = cls.old["v23_cert"]
        v26.DB_PATH = cls.old["v26_db"]
        v27.DB_PATH = cls.old["v27_db"]
        v27.DATA_DIR = cls.old["v27_data"]
        v27.BACKUP_DIR = cls.old["v27_backup"]
        cls.tmp.cleanup()

    def test_baseline_is_balanced_scored_and_replay_safe(self):
        started = v27.start_baseline(self.student_id)
        self.assertEqual(started["count"], 20)
        self.assertEqual(len({q["tool"] for q in started["questions"]}), 10)
        qmap = {q["id"]: q for q in v27.QUESTION_DATA["questions"]}
        answers = [{"id": q["id"], "answer": qmap[q["id"]]["answer"]} for q in started["questions"]]
        result = v27.submit_baseline(self.student_id, started["session_id"], answers)
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["classification"], "Advanced learner")
        with self.assertRaisesRegex(ValueError, "already completed"):
            v27.submit_baseline(self.student_id, started["session_id"], answers)
        with self.assertRaisesRegex(ValueError, "missing"):
            v27.submit_baseline(self.student_id + 99, started["session_id"], answers)

    def test_readiness_requires_core_items_but_not_ai_or_external_tools(self):
        status = v27.readiness_status(self.student_id, library_count=69, admin_configured=False)
        self.assertFalse(status["ready_to_learn"])
        self.assertFalse(next(x for x in status["steps"] if x["id"] == "ai")["required"])
        self.assertFalse(next(x for x in status["steps"] if x["id"] == "environment")["required"])
        with app.db_connect() as conn:
            conn.execute("INSERT OR IGNORE INTO student_profiles(student_id,target_role,study_minutes,interview_date,active_track,updated_at) VALUES(?,?,?,?,?,?)", (self.student_id,"Junior DevOps Engineer",90,"","devops",app.now_iso()))
            conn.execute("UPDATE student_profiles SET target_role=?,study_minutes=? WHERE student_id=?", ("Junior DevOps Engineer",90,self.student_id))
        # Complete a baseline, make a plan, configure admin, and create a verified backup.
        started = v27.start_baseline(self.student_id)
        qmap = {q["id"]: q for q in v27.QUESTION_DATA["questions"]}
        v27.submit_baseline(self.student_id, started["session_id"], [{"id":q["id"],"answer":qmap[q["id"]]["answer"]} for q in started["questions"]])
        v23.generate_daily_plan(self.student_id)
        v23.admin_setup("2468", "Admin", "Academy")
        v23.create_backup()
        ready = v27.readiness_status(self.student_id, library_count=69, admin_configured=True)
        self.assertTrue(ready["ready_to_learn"])
        self.assertTrue(ready["wizard_completed"])

    def test_passive_readiness_does_not_create_backup_audit_rows(self):
        with app.db_connect() as conn:
            before = conn.execute("SELECT COUNT(*) FROM backup_health_checks").fetchone()[0]
        v27.readiness_status(self.student_id, library_count=1, admin_configured=True)
        v27.readiness_status(self.student_id, library_count=1, admin_configured=True)
        with app.db_connect() as conn:
            after = conn.execute("SELECT COUNT(*) FROM backup_health_checks").fetchone()[0]
        self.assertEqual(before, after)
        v27.backup_health(record=True)
        with app.db_connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM backup_health_checks").fetchone()[0], after + 1)

    def test_environment_checker_uses_only_fixed_read_only_commands(self):
        def fake_which(name):
            return f"/safe/{name}" if name in {"python3", "git"} else None
        with mock.patch.object(v27.shutil, "which", side_effect=fake_which), mock.patch.object(v27, "_command_version", return_value="version ok") as version:
            result = v27.check_environment(self.student_id)
        self.assertTrue(result["core_ready"])
        self.assertEqual(next(x for x in result["tools"] if x["name"] == "python")["path"], "/safe/python3")
        commands = [call.args[0] for call in version.call_args_list]
        self.assertIn(["python3", "--version"], commands)
        self.assertIn(["git", "--version"], commands)
        self.assertTrue(all(isinstance(cmd, list) for cmd in commands))

    def test_backup_health_detects_tampering_and_never_accepts_arbitrary_path(self):
        backup = v23.create_backup()
        healthy = v27.backup_health(record=False)
        self.assertEqual(healthy["status"], "healthy")
        path = v27.BACKUP_DIR / backup["file_name"]
        path.write_bytes(path.read_bytes() + b"tampered")
        unhealthy = v27.backup_health(record=False)
        self.assertEqual(unhealthy["status"], "unhealthy")
        self.assertFalse(unhealthy["latest"]["checksum_ok"])

    def test_mastery_gates_begin_locked_and_require_nine_evidence_types(self):
        gates = v27.mastery_gates(self.student_id)
        self.assertEqual(gates["total_tools"], 21)
        self.assertEqual(gates["mastered_count"], 0)
        linux = next(x for x in gates["tools"] if x["tool"] == "linux")
        self.assertEqual(len(linux["requirements"]), 9)
        self.assertFalse(linux["mastered"])
        self.assertEqual({x["id"] for x in linux["requirements"]}, {"lessons","labs","test","practical","tickets","incident","capstone","interview","portfolio"})

    def test_freshness_requires_https_and_marks_old_current_content_due(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            v27.save_freshness({"tool":"linux","official_doc_url":"http://example.com"})
        old = (dt.date.today() - dt.timedelta(days=200)).isoformat()
        v27.save_freshness({"tool":"linux","review_status":"current","last_reviewed":old,"official_doc_url":"https://www.kernel.org/doc/html/latest/","reviewer":"Test"})
        item = next(x for x in v27.freshness_dashboard()["items"] if x["tool"] == "linux")
        self.assertEqual(item["effective_status"], "review_due")

    def test_provider_model_discovery_and_credit_free_fallback_dry_run(self):
        v26.save_provider({"provider":"gemini","enabled":True,"api_key":"AIza-test-key-123456789012345","daily_limit":100})
        payload = {"models":[
            {"name":"models/gemini-fast","displayName":"Fast","supportedGenerationMethods":["generateContent"],"inputTokenLimit":1000,"outputTokenLimit":200},
            {"name":"models/embed","supportedGenerationMethods":["embedContent"]},
        ]}
        with mock.patch.object(v26, "_http_get_json", return_value=(payload, 200)) as request:
            result = v26.discover_models("gemini")
        self.assertEqual([m["id"] for m in result["models"]], ["gemini-fast"])
        self.assertNotIn("AIza-test", json.dumps(result))
        self.assertTrue(request.called)
        v26.save_task_route("lesson_tutor", ["gemini", "openai"])
        dry = v26.fallback_chain_dry_run("lesson_tutor", ["gemini"])
        self.assertEqual(dry["credits_used"], 0)
        self.assertFalse(dry["would_succeed"])
        self.assertEqual(dry["trace"][0]["status"], "simulated_failure")

    def test_v27_tables_are_in_data_backup_allowlist(self):
        self.assertEqual(set(v27.backup_tables()), {"readiness_state","baseline_assessments","environment_checks","backup_health_checks","course_freshness"})


if __name__ == "__main__":
    unittest.main()
