"""
Unit tests for Billinger Core modules (Auth, Config, System Monitor, DB).
"""
import unittest
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.authentication.auth import auth_manager, AuthenticationError, AuthorizationError
from core.configuration.config import Config
from core.system_monitor import system_monitor
from storage.db import db
from storage.backup_manager import backup_manager

class TestCore(unittest.TestCase):
    def test_password_hashing(self):
        pwd = "ProductionSecret2026!"
        h, salt = auth_manager.hash_password(pwd)
        self.assertTrue(auth_manager.verify_password(pwd, h, salt))
        self.assertFalse(auth_manager.verify_password("WrongPassword", h, salt))

    def test_session_management(self):
        token = auth_manager.create_session("u123", "sunny_devops", "student")
        session = auth_manager.validate_session(token)
        self.assertEqual(session["username"], "sunny_devops")
        self.assertEqual(session["role"], "student")
        
        auth_manager.require_role(token, "student")
        with self.assertRaises(AuthorizationError):
            auth_manager.require_role(token, "admin")

    def test_system_monitor_stats(self):
        stats = system_monitor.get_system_stats()
        self.assertIn("platform", stats)
        self.assertIn("uptime_seconds", stats)
        self.assertIn("disk", stats)
        self.assertIn("memory", stats)
        self.assertIn("connectivity", stats)
        self.assertGreater(stats["disk"]["total_gb"], 0)

    def test_database_crud(self):
        test_user_id = f"test_usr_{int(time.time() * 1000)}"
        pwd_hash, salt = auth_manager.hash_password("Pass123!")
        db.execute("""
            INSERT INTO users (id, username, password_hash, salt, role, full_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_user_id, f"user_{test_user_id}", pwd_hash, salt, "student", "Test User", time.time()))

        row = db.fetchone("SELECT * FROM users WHERE id = ?", (test_user_id,))
        self.assertIsNotNone(row)
        self.assertEqual(row["full_name"], "Test User")

    def test_backup_and_integrity(self):
        backup_res = backup_manager.create_backup("test_suite")
        self.assertTrue(os.path.exists(backup_res["path"]))
        self.assertEqual(len(backup_res["sha256"]), 64)
