"""
Billinger Failure Injection & Graceful Recovery Tests.
"""
import unittest
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.router import ai_router
from storage.backup_manager import backup_manager

class TestFailureInjection(unittest.TestCase):
    def test_offline_ai_graceful_fallback(self):
        res = ai_router.route_request("complex_reasoning", "Diagnose network partition")
        self.assertIn("content", res)
        self.assertIn("model", res)

    def test_corrupt_backup_restoration_blocked(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(b"CORRUPTED_BINARY_HEADER_NOT_A_REAL_ZIP")
            corrupt_path = f.name
            
        chk_path = f"{corrupt_path}.sha256"
        with open(chk_path, "w") as f:
            f.write("deadbeef" * 8)

        try:
            with self.assertRaises(Exception):
                backup_manager.restore_backup(corrupt_path)
        finally:
            if os.path.exists(corrupt_path): os.remove(corrupt_path)
            if os.path.exists(chk_path): os.remove(chk_path)
