import subprocess
import os
import time
from pathlib import Path
from core.configuration.config import Config
from security.guard import command_guard
from core.errors.exceptions import SecurityViolationError

SANDBOX_DIR = Config.BASE_DIR / "labs" / "student_sandbox"

class SandboxRunner:
    def __init__(self, sandbox_dir: Path = None):
        self.sandbox_dir = sandbox_dir or SANDBOX_DIR
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

    def execute_command(self, command_str: str, timeout_sec: int = 15) -> dict:
        classification = command_guard.classify_command(command_str)
        if classification["level"] == "BLOCKED":
            raise SecurityViolationError(classification["reason"])

        start_time = time.time()
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C.UTF-8"
            env["LANG"] = "C.UTF-8"
            proc = subprocess.run(
                command_str,
                shell=True,
                cwd=str(self.sandbox_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_sec,
                env=env
            )
            elapsed = round(time.time() - start_time, 3)
            return {
                "command": command_str,
                "exit_code": proc.returncode,
                "stdout": proc.stdout[:32768],
                "stderr": proc.stderr[:32768],
                "elapsed_seconds": elapsed,
                "risk_level": classification["level"],
                "timed_out": False
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command_str,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_sec} seconds.",
                "elapsed_seconds": timeout_sec,
                "risk_level": classification["level"],
                "timed_out": True
            }
        except Exception as e:
            return {
                "command": command_str,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "elapsed_seconds": round(time.time() - start_time, 3),
                "risk_level": classification["level"],
                "timed_out": False
            }

sandbox_runner = SandboxRunner()
