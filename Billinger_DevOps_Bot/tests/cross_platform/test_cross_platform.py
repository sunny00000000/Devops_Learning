"""
Cross-Platform Verification Suite (Windows & Linux).
"""
import unittest
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.configuration.config import Config

class TestCrossPlatform(unittest.TestCase):
    def test_linux_scripts_executable(self):
        scripts = ["start_billinger.sh", "setup_portable_runtime.sh", "run_self_test.sh"]
        for s in scripts:
            p = Config.BASE_DIR / s
            self.assertTrue(p.exists(), f"Missing Linux script: {s}")
            self.assertTrue(os.access(str(p), os.X_OK), f"Script not executable: {s}")

    def test_bash_syntax_check(self):
        scripts = ["start_billinger.sh", "setup_portable_runtime.sh", "run_self_test.sh"]
        for s in scripts:
            p = Config.BASE_DIR / s
            res = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Bash syntax error in {s}: {res.stderr}")

    def test_windows_scripts_exist(self):
        win_scripts = [
            "Start_Billinger_Bot.bat", "Start_Billinger_Bot.ps1",
            "Setup_Portable_Runtime.bat", "Setup_Portable_Runtime.ps1",
            "Run_Self_Test.bat"
        ]
        for s in win_scripts:
            p = Config.BASE_DIR / s
            self.assertTrue(p.exists(), f"Missing Windows script: {s}")
            content = p.read_text(encoding="utf-8")
            self.assertIn("python", content.lower())
